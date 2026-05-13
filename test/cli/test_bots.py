"""cli/bots.py 테스트 — bots.yaml 파싱 및 검증."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from cli.bots import BotsConfig, BotConfig, RiskConfig, load_bots_config, validate_bots_config


# ── 픽스처 ───────────────────────────────────────────────────────────

def _write_yaml(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "bots.yaml"
    p.write_text(yaml.dump(data), encoding="utf-8")
    return p


def _valid_data():
    return {
        "bots": [
            {"name": "bot_a", "strategy": "momentum_topn_v1", "universe": "snp500",
             "capital_pct": 0.4, "rebalance": "weekly"},
            {"name": "bot_b", "strategy": "low_volatility", "universe": "sector_etf",
             "capital_pct": 0.3, "rebalance": "monthly"},
        ],
        "risk": {"daily_loss_limit_pct": 0.05, "max_drawdown_pct": 0.20},
    }


# ── load_bots_config ─────────────────────────────────────────────────

class TestLoadBotsConfig:
    def test_loads_valid_file(self, tmp_path):
        path = _write_yaml(tmp_path, _valid_data())
        cfg = load_bots_config(path)
        assert len(cfg.bots) == 2
        assert cfg.bots[0].name == "bot_a"

    def test_bot_fields_parsed(self, tmp_path):
        path = _write_yaml(tmp_path, _valid_data())
        cfg = load_bots_config(path)
        b = cfg.bots[0]
        assert b.strategy == "momentum_topn_v1"
        assert b.universe == "snp500"
        assert b.capital_pct == pytest.approx(0.4)
        assert b.rebalance == "weekly"

    def test_risk_defaults_used_if_absent(self, tmp_path):
        data = {"bots": [
            {"name": "b", "strategy": "momentum_topn_v1", "universe": "snp500",
             "capital_pct": 0.5, "rebalance": "monthly"},
        ]}
        path = _write_yaml(tmp_path, data)
        cfg = load_bots_config(path)
        assert cfg.risk.daily_loss_limit_pct == pytest.approx(0.05)
        assert cfg.risk.max_drawdown_pct == pytest.approx(0.20)

    def test_risk_values_loaded(self, tmp_path):
        data = _valid_data()
        data["risk"] = {"daily_loss_limit_pct": 0.03, "max_drawdown_pct": 0.15}
        path = _write_yaml(tmp_path, data)
        cfg = load_bots_config(path)
        assert cfg.risk.daily_loss_limit_pct == pytest.approx(0.03)

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_bots_config(tmp_path / "nonexistent.yaml")

    def test_optional_params_field(self, tmp_path):
        data = {"bots": [
            {"name": "b", "strategy": "momentum_topn_v1", "universe": "snp500",
             "capital_pct": 0.5, "rebalance": "monthly",
             "params": {"top_n": 5}},
        ]}
        path = _write_yaml(tmp_path, data)
        cfg = load_bots_config(path)
        assert cfg.bots[0].params == {"top_n": 5}

    def test_params_defaults_to_empty_dict(self, tmp_path):
        path = _write_yaml(tmp_path, _valid_data())
        cfg = load_bots_config(path)
        assert cfg.bots[0].params == {}

    def test_rebalance_defaults_to_monthly(self, tmp_path):
        data = {"bots": [
            {"name": "b", "strategy": "momentum_topn_v1", "universe": "snp500",
             "capital_pct": 0.5},  # rebalance 생략
        ]}
        path = _write_yaml(tmp_path, data)
        cfg = load_bots_config(path)
        assert cfg.bots[0].rebalance == "monthly"


# ── validate_bots_config ─────────────────────────────────────────────

def _make_cfg(**overrides) -> BotsConfig:
    defaults = dict(
        name="bot_a", strategy="momentum_topn_v1", universe="snp500",
        capital_pct=0.5, rebalance="monthly",
    )
    defaults.update(overrides)
    return BotsConfig(
        bots=[BotConfig(**defaults)],
        risk=RiskConfig(),
    )


class TestValidateBotsConfig:
    def test_valid_config_passes(self, tmp_path):
        path = _write_yaml(tmp_path, _valid_data())
        cfg = load_bots_config(path)
        validate_bots_config(cfg)  # 예외 없어야 함

    # capital_pct 합계
    def test_capital_pct_sum_exactly_one_passes(self):
        cfg = BotsConfig(
            bots=[
                BotConfig("a", "momentum_topn_v1", "snp500", 0.6, "monthly"),
                BotConfig("b", "low_volatility", "sector_etf", 0.4, "monthly"),
            ],
            risk=RiskConfig(),
        )
        validate_bots_config(cfg)

    def test_capital_pct_sum_under_one_passes(self):
        validate_bots_config(_make_cfg(capital_pct=0.7))

    def test_capital_pct_sum_over_one_raises(self):
        cfg = BotsConfig(
            bots=[
                BotConfig("a", "momentum_topn_v1", "snp500", 0.6, "monthly"),
                BotConfig("b", "low_volatility", "sector_etf", 0.6, "monthly"),
            ],
            risk=RiskConfig(),
        )
        with pytest.raises(ValueError, match="capital_pct 합계"):
            validate_bots_config(cfg)

    # 전략 이름
    def test_unknown_strategy_raises(self):
        with pytest.raises(ValueError, match="알 수 없는 전략"):
            validate_bots_config(_make_cfg(strategy="fake_strategy_xyz"))

    def test_long_form_strategy_name_valid(self):
        validate_bots_config(_make_cfg(strategy="rsi_mean_reversion_v1"))

    def test_short_form_strategy_name_valid(self):
        validate_bots_config(_make_cfg(strategy="momentum"))

    # 유니버스
    def test_unknown_universe_raises(self):
        with pytest.raises(ValueError, match="알 수 없는 유니버스"):
            validate_bots_config(_make_cfg(universe="nasdaq100"))

    def test_snp500_universe_valid(self):
        validate_bots_config(_make_cfg(universe="snp500"))

    def test_sector_etf_universe_valid(self):
        validate_bots_config(_make_cfg(universe="sector_etf"))

    # 리밸런싱 주기
    def test_invalid_rebalance_raises(self):
        with pytest.raises(ValueError, match="알 수 없는 리밸런싱"):
            validate_bots_config(_make_cfg(rebalance="yearly"))

    def test_daily_rebalance_valid(self):
        validate_bots_config(_make_cfg(capital_pct=0.3, rebalance="daily"))

    # 봇 이름 중복
    def test_duplicate_bot_name_raises(self):
        cfg = BotsConfig(
            bots=[
                BotConfig("same_name", "momentum_topn_v1", "snp500", 0.3, "monthly"),
                BotConfig("same_name", "low_volatility", "sector_etf", 0.3, "monthly"),
            ],
            risk=RiskConfig(),
        )
        with pytest.raises(ValueError, match="중복"):
            validate_bots_config(cfg)

    # capital_pct 범위
    def test_zero_capital_pct_raises(self):
        with pytest.raises(ValueError, match="capital_pct"):
            validate_bots_config(_make_cfg(capital_pct=0.0))

    def test_negative_capital_pct_raises(self):
        with pytest.raises(ValueError, match="capital_pct"):
            validate_bots_config(_make_cfg(capital_pct=-0.1))

    def test_capital_pct_exactly_one_valid(self):
        validate_bots_config(_make_cfg(capital_pct=1.0))

    # 복수 오류 시 한 번에 보고
    def test_multiple_errors_reported_together(self):
        cfg = BotsConfig(
            bots=[
                BotConfig("bot", "fake_strategy", "fake_universe", -0.1, "yearly"),
            ],
            risk=RiskConfig(),
        )
        with pytest.raises(ValueError) as exc_info:
            validate_bots_config(cfg)
        msg = str(exc_info.value)
        # 여러 오류가 한 메시지에 포함돼야 함
        assert "전략" in msg or "유니버스" in msg or "capital_pct" in msg

    def test_empty_bots_list_passes(self):
        cfg = BotsConfig(bots=[], risk=RiskConfig())
        validate_bots_config(cfg)  # 빈 리스트는 합계 0.0 ≤ 1.0 → 통과
