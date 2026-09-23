# AUTO-GENERATED — do not edit by hand.
# Source: backend/scripts/generate_ontology_python.py
# Re-run with: cd backend && python scripts/generate_ontology_python.py
# Drift detector: backend/tests/test_ontology_python_codegen.py
"""Typed shapes of the Nyquist ontology, as the API serialises them.

Standard library only. ``datetime``/``date`` properties arrive as ISO-8601
strings and are typed ``str``; ``NotRequired`` marks fields the backend may
omit; ``| None`` marks fields it may send as null.
"""
from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict

# --- Literal unions (kind discriminators) ---

ObjectKind = Literal[
    'agent_verdict',
    'analysis_run',
    'backtest_result',
    'case',
    'check',
    'check_report',
    'committee_pack',
    'correlation_matrix',
    'counterparty',
    'credit_event_record',
    'csa_margin_call',
    'data_build',
    'data_job',
    'data_schedule',
    'data_source',
    'decision',
    'execution_analytics',
    'execution_quality_report',
    'factor_model_fit',
    'geo_entity',
    'greek_snapshot',
    'hedge_program',
    'indicator',
    'instrument',
    'instrument_valuation',
    'joint_scenario_sample',
    'margin_requirement',
    'model_calibration',
    'observation',
    'operational_picture',
    'order_attestation',
    'otc_structured_trade',
    'pe_fund',
    'point_process_fit',
    'portfolio_company',
    'portfolio_optimization',
    'position',
    'pricing_model',
    'regime_state',
    'regulatory_norm',
    'risk_limit',
    'scenario',
    'scenario_detection',
    'sensor',
    'settlement_instruction',
    'stress_scenario',
    'stress_test_result',
    'trade',
    'transform_run',
    'var_report',
    'vol_surface',
    'volatility_estimate',
    'wiki_page',
    'yield_curve',
]

LinkKind = Literal[
    'backtested_on',
    'belongs_to',
    'between',
    'calibrated_on',
    'cites',
    'compliant_with',
    'computed_for',
    'constrained_by',
    'covers',
    'decision_about',
    'derived_from',
    'evidenced_by',
    'executed_for',
    'executed_via',
    'factor_loaded_on',
    'flow_observed_in',
    'has_underlying',
    'hedged_by',
    'held_by',
    'holds_portco',
    'influences',
    'issued_by',
    'located_in',
    'margin_required_for',
    'measures',
    'observed_by',
    'optimized_over',
    'priced_with',
    'produced',
    'published_by',
    'references',
    'regime_classified',
    'sampled_with',
    'stressed_by',
    'uses_market_data',
    'uses_model',
    'valued_as',
    'valued_with_model',
    'verdict_about',
    'vol_estimated_for',
]

OBJECT_KINDS: tuple[ObjectKind, ...] = (
    'agent_verdict',
    'analysis_run',
    'backtest_result',
    'case',
    'check',
    'check_report',
    'committee_pack',
    'correlation_matrix',
    'counterparty',
    'credit_event_record',
    'csa_margin_call',
    'data_build',
    'data_job',
    'data_schedule',
    'data_source',
    'decision',
    'execution_analytics',
    'execution_quality_report',
    'factor_model_fit',
    'geo_entity',
    'greek_snapshot',
    'hedge_program',
    'indicator',
    'instrument',
    'instrument_valuation',
    'joint_scenario_sample',
    'margin_requirement',
    'model_calibration',
    'observation',
    'operational_picture',
    'order_attestation',
    'otc_structured_trade',
    'pe_fund',
    'point_process_fit',
    'portfolio_company',
    'portfolio_optimization',
    'position',
    'pricing_model',
    'regime_state',
    'regulatory_norm',
    'risk_limit',
    'scenario',
    'scenario_detection',
    'sensor',
    'settlement_instruction',
    'stress_scenario',
    'stress_test_result',
    'trade',
    'transform_run',
    'var_report',
    'vol_surface',
    'volatility_estimate',
    'wiki_page',
    'yield_curve',
)

LINK_KINDS: tuple[LinkKind, ...] = (
    'backtested_on',
    'belongs_to',
    'between',
    'calibrated_on',
    'cites',
    'compliant_with',
    'computed_for',
    'constrained_by',
    'covers',
    'decision_about',
    'derived_from',
    'evidenced_by',
    'executed_for',
    'executed_via',
    'factor_loaded_on',
    'flow_observed_in',
    'has_underlying',
    'hedged_by',
    'held_by',
    'holds_portco',
    'influences',
    'issued_by',
    'located_in',
    'margin_required_for',
    'measures',
    'observed_by',
    'optimized_over',
    'priced_with',
    'produced',
    'published_by',
    'references',
    'regime_classified',
    'sampled_with',
    'stressed_by',
    'uses_market_data',
    'uses_model',
    'valued_as',
    'valued_with_model',
    'verdict_about',
    'vol_estimated_for',
)


# --- Object types — one TypedDict per kind ---


class AgentVerdict(TypedDict):
    """Object kind ``agent_verdict`` — title field ``topic``."""

    object_id: str
    kind: NotRequired[Literal['agent_verdict']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    agent_id: str
    topic: str
    verdict_text: str
    confidence: NotRequired[float | None]
    model_id: NotRequired[str | None]
    provider: NotRequired[str | None]
    prompt_tokens: NotRequired[int | None]
    completion_tokens: NotRequired[int | None]
    voice_drift: NotRequired[list[Any]]
    tool_calls: NotRequired[list[Any]]
    citations: NotRequired[list[Any]]
    as_of: str
    attributes: NotRequired[dict[str, Any]]


class AnalysisRun(TypedDict):
    """Object kind ``analysis_run`` — title field ``label``."""

    object_id: str
    kind: NotRequired[Literal['analysis_run']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    run_id: str
    label: str
    route: NotRequired[str | None]
    request_id: NotRequired[str | None]
    actor_id: NotRequired[str | None]
    auth_kind: NotRequired[Literal['jwt', 'api_key', 'demo_guest', 'dev'] | None]
    tenant_id: NotRequired[str | None]
    status: Literal['ok', 'error']
    error_type: NotRequired[str | None]
    error_message: NotRequired[str | None]
    started_at: NotRequired[str | None]
    finished_at: str
    duration_ms: NotRequired[float | None]
    inputs_digest: NotRequired[str | None]
    inputs: NotRequired[dict[str, Any] | None]
    inputs_truncated: NotRequired[bool]
    result_urns: NotRequired[list[Any]]
    as_of: str
    attributes: NotRequired[dict[str, Any]]


class BacktestResult(TypedDict):
    """Object kind ``backtest_result`` — no title field."""

    object_id: str
    kind: NotRequired[Literal['backtest_result']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    strategy_urn: NotRequired[str | None]
    portfolio_urn: NotRequired[str | None]
    total_return: float
    cagr: NotRequired[float | None]
    sharpe_ratio: NotRequired[float | None]
    sortino_ratio: NotRequired[float | None]
    calmar_ratio: NotRequired[float | None]
    information_ratio: NotRequired[float | None]
    volatility: NotRequired[float | None]
    max_drawdown: NotRequired[float | None]
    win_rate: NotRequired[float | None]
    profit_factor: NotRequired[float | None]
    initial_capital: NotRequired[float | None]
    n_observations: NotRequired[int | None]
    start_date: NotRequired[str | None]
    end_date: NotRequired[str | None]
    as_of: str
    currency: NotRequired[str]
    attributes: NotRequired[dict[str, Any]]


class Case(TypedDict):
    """Object kind ``case`` — title field ``title``."""

    object_id: str
    kind: NotRequired[Literal['case']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    title: str
    case_id: str
    actor_id: str
    tenant_id: NotRequired[str | None]
    opened_at: str
    pinned_urns: NotRequired[list[Any]]
    notes: NotRequired[str]
    status: NotRequired[Literal['open', 'closed']]
    closed_at: NotRequired[str | None]
    resolution: NotRequired[str]
    as_of: str
    attributes: NotRequired[dict[str, Any]]


class Check(TypedDict):
    """Object kind ``check`` — no title field."""

    rid: str
    kind: NotRequired[Literal['check']]
    rule: str
    config: NotRequired[dict[str, Any]]
    intent: Literal['MONITORING', 'GATING']
    groups: NotRequired[list[Any]]
    target: NotRequired[str | None]
    description: NotRequired[str]
    enabled: NotRequired[bool]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    created_at: NotRequired[str]


class CheckReport(TypedDict):
    """Object kind ``check_report`` — no title field."""

    rid: str
    kind: NotRequired[Literal['check_report']]
    check_rid: str
    rule: str
    status: Literal[
        'PASSED',
        'FAILED',
        'WARNING',
        'ERROR',
        'NOT_APPLICABLE',
        'NOT_COMPUTABLE',
    ]
    intent: Literal['MONITORING', 'GATING']
    groups: NotRequired[list[Any]]
    target: NotRequired[str | None]
    detail: NotRequired[str]
    observed: NotRequired[float | None]
    threshold: NotRequired[float | None]
    config: NotRequired[dict[str, Any]]
    config_hash: str
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    checked_at: NotRequired[str]


class CommitteePack(TypedDict):
    """Object kind ``committee_pack`` — title field ``label``."""

    object_id: str
    kind: NotRequired[Literal['committee_pack']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    label: str
    pack_id: str
    owner_id: str
    generated_at: str
    run_urns: NotRequired[list[Any]]
    decision_ids: NotRequired[list[Any]]
    inputs_hash: str
    counts: NotRequired[dict[str, Any]]
    as_of: str
    attributes: NotRequired[dict[str, Any]]


class CorrelationMatrix(TypedDict):
    """Object kind ``correlation_matrix`` — no title field."""

    object_id: str
    kind: NotRequired[Literal['correlation_matrix']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    method: NotRequired[Literal['historical', 'ewma', 'implied', 'shrinkage']]
    snapshot_at: str
    window_days: NotRequired[int | None]
    assets: NotRequired[list[Any]]
    matrix: NotRequired[list[Any]]
    attributes: NotRequired[dict[str, Any]]


class Counterparty(TypedDict):
    """Object kind ``counterparty`` — title field ``legal_name``."""

    object_id: str
    kind: NotRequired[Literal['counterparty']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    legal_name: str
    lei: NotRequired[str | None]
    jurisdiction: str


class CreditEventRecord(TypedDict):
    """Object kind ``credit_event_record`` — no title field."""

    object_id: str
    kind: NotRequired[Literal['credit_event_record']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    counterparty_urn: str
    event_type: Literal[
        'default',
        'bankruptcy',
        'restructuring',
        'downgrade',
        'cross_default',
        'rating_watch',
        'other',
    ]
    observed_at: str
    severity: NotRequired[Literal['low', 'medium', 'high', 'critical']]
    source: NotRequired[str | None]
    attributes: NotRequired[dict[str, Any]]


class CsaMarginCall(TypedDict):
    """Object kind ``csa_margin_call`` — no title field."""

    object_id: str
    kind: NotRequired[Literal['csa_margin_call']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    counterparty_urn: str
    exposure_usd: float
    threshold_usd: float
    call_amount_usd: float
    direction: Literal['call', 'return']
    issued_at: str
    status: NotRequired[Literal['issued', 'satisfied', 'disputed', 'expired']]
    csa_id: NotRequired[str | None]
    attributes: NotRequired[dict[str, Any]]


class DataBuild(TypedDict):
    """Object kind ``data_build`` — title field ``job_id``."""

    object_id: str
    kind: NotRequired[Literal['data_build']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    job_id: str
    job_hash: str
    schedule_id: NotRequired[str | None]
    status: Literal['running', 'succeeded', 'partial', 'aborted']
    started_at: str
    finished_at: NotRequired[str | None]
    built: NotRequired[list[Any]]
    skipped: NotRequired[dict[str, Any]]
    failed: NotRequired[dict[str, Any]]
    attempts: NotRequired[dict[str, Any]]
    actor: NotRequired[str]
    attributes: NotRequired[dict[str, Any]]


class DataJob(TypedDict):
    """Object kind ``data_job`` — title field ``job_id``."""

    object_id: str
    kind: NotRequired[Literal['data_job']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    job_id: str
    job_hash: str
    semantic_version: str
    target_kind: Literal['manual', 'upstream', 'connecting']
    roots: NotRequired[list[Any]]
    to: NotRequired[list[Any]]
    abort_on_failure: NotRequired[bool]
    max_attempts: NotRequired[int]
    owner: NotRequired[str | None]
    attributes: NotRequired[dict[str, Any]]


class DataSchedule(TypedDict):
    """Object kind ``data_schedule`` — title field ``schedule_id``."""

    object_id: str
    kind: NotRequired[Literal['data_schedule']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    schedule_id: str
    job_id: str
    schedule_hash: str
    semantic_version: str
    trigger_kind: str
    enabled: NotRequired[bool]
    disabled_reason: NotRequired[str | None]
    owner: NotRequired[str | None]
    attributes: NotRequired[dict[str, Any]]


class DataSource(TypedDict):
    """Object kind ``data_source`` — title field ``name``."""

    object_id: str
    kind: NotRequired[Literal['data_source']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    name: str
    homepage: NotRequired[str | None]
    license: NotRequired[str | None]
    sla_seconds: NotRequired[int | None]
    attributes: NotRequired[dict[str, Any]]


class Decision(TypedDict):
    """Object kind ``decision`` — title field ``label``."""

    object_id: str
    kind: NotRequired[Literal['decision']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    label: str
    decision_id: str
    owner_id: str
    tenant_id: NotRequired[str | None]
    target_urn: str
    symbol: NotRequired[str | None]
    direction: Literal['long', 'short', 'neutral', 'avoid']
    horizon_days: int
    confidence: NotRequired[float | None]
    decided_at: str
    supersedes_id: NotRequired[str | None]
    as_of: str
    attributes: NotRequired[dict[str, Any]]


class ExecutionAnalytics(TypedDict):
    """Object kind ``execution_analytics`` — no title field."""

    object_id: str
    kind: NotRequired[Literal['execution_analytics']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    instrument_urn: str
    mode: Literal[
        'pretrade_estimate',
        'almgren_chriss_optimal',
        'strategy_comparison',
        'monte_carlo_simulation',
        'frontier_summary',
        'other',
    ]
    side: NotRequired[Literal['buy', 'sell', 'unspecified']]
    quantity: NotRequired[float | None]
    notional_usd: NotRequired[float | None]
    expected_impact_bps: NotRequired[float | None]
    expected_cost_bps: NotRequired[float | None]
    timing_risk_bps: NotRequired[float | None]
    permanent_bps: NotRequired[float | None]
    temporary_bps: NotRequired[float | None]
    liquidity_composite: NotRequired[int | None]
    horizon_days: NotRequired[float | None]
    n_steps: NotRequired[int | None]
    risk_aversion: NotRequired[float | None]
    strategy_label: NotRequired[str | None]
    recommended_algos: NotRequired[list[Any]]
    as_of: str
    attributes: NotRequired[dict[str, Any]]


class ExecutionQualityReport(TypedDict):
    """Object kind ``execution_quality_report`` — no title field."""

    object_id: str
    kind: NotRequired[Literal['execution_quality_report']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    instrument_urn: str
    arrival_price: NotRequired[float | None]
    avg_fill_price: NotRequired[float | None]
    implementation_shortfall_bps: NotRequired[float | None]
    slippage_bps: NotRequired[float | None]
    filled_quantity: NotRequired[float | None]
    notional_usd: NotRequired[float | None]
    venue: NotRequired[str | None]
    benchmark: NotRequired[str | None]
    as_of: str
    attributes: NotRequired[dict[str, Any]]


class FactorModelFit(TypedDict):
    """Object kind ``factor_model_fit`` — no title field."""

    object_id: str
    kind: NotRequired[Literal['factor_model_fit']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    method: Literal[
        'fama_macbeth',
        'pca_eigenportfolio',
        'ledoit_wolf_shrinkage',
        'other',
    ]
    universe_urn: str
    n_assets: int
    n_factors: int
    n_periods: NotRequired[int | None]
    mean_r2: NotRequired[float | None]
    grs_p_value: NotRequired[float | None]
    grs_rejects_h0: NotRequired[bool | None]
    explained_variance_pc1: NotRequired[float | None]
    n_components_signal: NotRequired[int | None]
    shrinkage_alpha: NotRequired[float | None]
    factor_names: NotRequired[list[Any]]
    as_of: str
    attributes: NotRequired[dict[str, Any]]


class GeoEntity(TypedDict):
    """Object kind ``geo_entity`` — title field ``name``."""

    lat: NotRequired[float | None]
    lon: NotRequired[float | None]
    radius_km: NotRequired[float | None]
    object_id: str
    kind: NotRequired[Literal['geo_entity']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    name: str
    geo_kind: Literal[
        'country',
        'region',
        'city',
        'port',
        'basin',
        'mining_area',
        'asset_site',
        'exclusive_economic_zone',
        'other',
    ]
    iso_code: NotRequired[str | None]
    parent_id: NotRequired[str | None]
    attributes: NotRequired[dict[str, Any]]


class GreekSnapshot(TypedDict):
    """Object kind ``greek_snapshot`` — no title field."""

    object_id: str
    kind: NotRequired[Literal['greek_snapshot']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    target_urn: str
    delta: NotRequired[float | None]
    gamma: NotRequired[float | None]
    vega: NotRequired[float | None]
    theta: NotRequired[float | None]
    rho: NotRequired[float | None]
    as_of: str
    attributes: NotRequired[dict[str, Any]]


class HedgeProgram(TypedDict):
    """Object kind ``hedge_program`` — no title field."""

    object_id: str
    kind: NotRequired[Literal['hedge_program']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    portfolio_urn: str
    method: Literal[
        'delta_neutral',
        'delta_gamma',
        'static_replication',
        'dynamic_delta',
        'quadratic_minvar',
        'rl_policy',
        'hjb_optimal',
        'other',
    ]
    target_metric: NotRequired[Literal[
        'delta',
        'gamma',
        'vega',
        'duration',
        'var',
        'cvar',
        'other',
    ]]
    target_value: NotRequired[float | None]
    residual_value: NotRequired[float | None]
    hedge_instrument_urn: NotRequired[str | None]
    hedge_quantity: NotRequired[float | None]
    hedge_cost_bps: NotRequired[float | None]
    expected_tracking_error: NotRequired[float | None]
    rebalance_horizon_days: NotRequired[float | None]
    n_steps: NotRequired[int | None]
    risk_aversion: NotRequired[float | None]
    as_of: str
    attributes: NotRequired[dict[str, Any]]


class Indicator(TypedDict):
    """Object kind ``indicator`` — title field ``indicator_key``."""

    object_id: str
    kind: NotRequired[Literal['indicator']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    indicator_key: str
    description: str
    unit: NotRequired[str | None]
    cadence: NotRequired[Literal[
        'realtime',
        'hourly',
        'daily',
        'weekly',
        'monthly',
        'irregular',
    ]]
    attributes: NotRequired[dict[str, Any]]


class Instrument(TypedDict):
    """Object kind ``instrument`` — title field ``ticker``."""

    object_id: str
    kind: NotRequired[Literal['instrument']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    isin: NotRequired[str | None]
    ticker: NotRequired[str | None]
    asset_class: str
    currency: str
    attributes: NotRequired[dict[str, Any]]


class InstrumentValuation(TypedDict):
    """Object kind ``instrument_valuation`` — no title field."""

    object_id: str
    kind: NotRequired[Literal['instrument_valuation']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    instrument_urn: str
    pricing_model_urn: NotRequired[str | None]
    model_family: Literal[
        'bsm',
        'heston',
        'merton',
        'bates',
        'sabr',
        'vg',
        'dcf',
        'cost_of_carry',
        'swap_dcf',
        'fx_swap',
        'other',
    ]
    valuation_kind: Literal[
        'option',
        'swap',
        'fx_swap',
        'bond',
        'forward',
        'future',
    ]
    value: float
    currency: NotRequired[str]
    delta: NotRequired[float | None]
    gamma: NotRequired[float | None]
    vega: NotRequired[float | None]
    theta: NotRequired[float | None]
    rho: NotRequired[float | None]
    duration: NotRequired[float | None]
    modified_duration: NotRequired[float | None]
    convexity: NotRequired[float | None]
    dv01: NotRequired[float | None]
    ytm: NotRequired[float | None]
    fair_value: NotRequired[float | None]
    intrinsic_value: NotRequired[float | None]
    as_of: str
    attributes: NotRequired[dict[str, Any]]


class JointScenarioSample(TypedDict):
    """Object kind ``joint_scenario_sample`` — no title field."""

    object_id: str
    kind: NotRequired[Literal['joint_scenario_sample']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    method: Literal[
        'gaussian_copula',
        't_copula',
        'vine_copula',
        'archimedean_copula',
        'empirical',
    ]
    n_samples: int
    dim: int
    assets: NotRequired[list[Any]]
    summary: NotRequired[dict[str, Any]]
    seed: NotRequired[int | None]
    sample_digest: NotRequired[str | None]
    snapshot_at: str
    attributes: NotRequired[dict[str, Any]]


class MarginRequirement(TypedDict):
    """Object kind ``margin_requirement`` — no title field."""

    object_id: str
    kind: NotRequired[Literal['margin_requirement']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    portfolio_urn: str
    regime: Literal[
        'isda_simm_delta',
        'isda_simm_vega',
        'isda_simm_curvature',
        'isda_simm_total',
        'frtb_ima',
        'house_im',
        'ucits_haircut',
        'exchange_im',
        'other',
    ]
    margin_value: float
    currency: NotRequired[str]
    n_buckets: NotRequired[int | None]
    n_risk_factors: NotRequired[int | None]
    as_of: str
    attributes: NotRequired[dict[str, Any]]


class ModelCalibration(TypedDict):
    """Object kind ``model_calibration`` — no title field."""

    object_id: str
    kind: NotRequired[Literal['model_calibration']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    model_urn: str
    market_data_urn: NotRequired[str | None]
    calibrated_at: str
    params: NotRequired[dict[str, Any]]
    rmse: NotRequired[float | None]
    attributes: NotRequired[dict[str, Any]]


class Observation(TypedDict):
    """Object kind ``observation`` — title field ``phenomenon``."""

    lat: NotRequired[float | None]
    lon: NotRequired[float | None]
    radius_km: NotRequired[float | None]
    object_id: str
    kind: NotRequired[Literal['observation']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    phenomenon: str
    observed_at: str
    value: NotRequired[float | None]
    unit: NotRequired[str | None]
    attributes: NotRequired[dict[str, Any]]


class OperationalPicture(TypedDict):
    """Object kind ``operational_picture`` — title field ``alert_level``."""

    object_id: str
    kind: NotRequired[Literal['operational_picture']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    alert_level: Literal['green', 'amber', 'red']
    composite_score: float
    n_green: int
    n_amber: int
    n_red: int
    worst_pillar: NotRequired[str | None]
    n_actions: int
    as_of: str
    attributes: NotRequired[dict[str, Any]]


class OrderAttestation(TypedDict):
    """Object kind ``order_attestation`` — title field ``attestation_id``."""

    object_id: str
    kind: NotRequired[Literal['order_attestation']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    attestation_id: str
    verdict: Literal['approved', 'denied']
    denial_reason: NotRequired[str | None]
    canonical_payload_hash: str
    checks_passed: int
    checks_failed: int
    checks_skipped: int
    order_id: NotRequired[str | None]
    strategy_id: NotRequired[str | None]
    instrument: NotRequired[str | None]
    notional_usd: NotRequired[float | None]
    as_of: str
    attributes: NotRequired[dict[str, Any]]


class OtcStructuredTrade(TypedDict):
    """Object kind ``otc_structured_trade`` — no title field."""

    object_id: str
    kind: NotRequired[Literal['otc_structured_trade']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    counterparty_urn: str
    structure: Literal[
        'single_leg',
        'multi_leg',
        'swap',
        'option_strip',
        'basket',
        'structured_note',
        'other',
    ]
    notional_usd: float
    trade_date: str
    status: NotRequired[Literal[
        'quoted',
        'confirmed',
        'settled',
        'pending_unwind',
        'unwound',
        'cancelled',
    ]]
    legs: NotRequired[list[Any]]
    csa_id: NotRequired[str | None]
    attributes: NotRequired[dict[str, Any]]


class PeFund(TypedDict):
    """Object kind ``pe_fund`` — title field ``name``."""

    object_id: str
    kind: NotRequired[Literal['pe_fund']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    name: str
    vintage_year: NotRequired[int | None]
    commitment: NotRequired[float | None]
    currency: NotRequired[str | None]
    strategy: NotRequired[str | None]
    manager: NotRequired[str | None]
    as_of: str
    attributes: NotRequired[dict[str, Any]]


class PointProcessFit(TypedDict):
    """Object kind ``point_process_fit`` — no title field."""

    object_id: str
    kind: NotRequired[Literal['point_process_fit']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    instrument_urn: str
    process_kind: Literal['hawkes_univariate', 'hawkes_bivariate_ofi']
    mu: float
    alpha: float
    beta: float
    branching_ratio: float
    half_life: NotRequired[float | None]
    n_events: int
    log_likelihood: NotRequired[float | None]
    aic: NotRequired[float | None]
    bic: NotRequired[float | None]
    imbalance_ratio: NotRequired[float | None]
    cross_correlation: NotRequired[float | None]
    n_toxic_periods: NotRequired[int | None]
    as_of: str
    attributes: NotRequired[dict[str, Any]]


class PortfolioCompany(TypedDict):
    """Object kind ``portfolio_company`` — title field ``name``."""

    object_id: str
    kind: NotRequired[Literal['portfolio_company']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    name: str
    sector: NotRequired[str | None]
    country: NotRequired[str | None]
    entry_date: NotRequired[str | None]
    exit_date: NotRequired[str | None]
    as_of: str
    attributes: NotRequired[dict[str, Any]]


class PortfolioOptimization(TypedDict):
    """Object kind ``portfolio_optimization`` — no title field."""

    object_id: str
    kind: NotRequired[Literal['portfolio_optimization']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    method: Literal[
        'black_litterman',
        'min_variance',
        'max_sharpe',
        'mean_variance',
        'cvar',
        'risk_parity',
        'kelly',
        'equal_weight',
        'other',
    ]
    universe_urn: str
    n_assets: int
    expected_return: NotRequired[float | None]
    volatility: NotRequired[float | None]
    sharpe_ratio: NotRequired[float | None]
    cvar: NotRequired[float | None]
    num_positions: NotRequired[int | None]
    effective_n: NotRequired[float | None]
    diversification_ratio: NotRequired[float | None]
    max_weight: NotRequired[float | None]
    leverage: NotRequired[float | None]
    long_only: NotRequired[bool | None]
    top_holdings: NotRequired[list[Any]]
    as_of: str
    attributes: NotRequired[dict[str, Any]]


class Position(TypedDict):
    """Object kind ``position`` — no title field."""

    object_id: str
    kind: NotRequired[Literal['position']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    notional: float
    quantity: float
    as_of: str


class PricingModel(TypedDict):
    """Object kind ``pricing_model`` — no title field."""

    object_id: str
    kind: NotRequired[Literal['pricing_model']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    model_family: Literal[
        'heston',
        'sabr',
        'levy',
        'black_scholes',
        'hull_white',
        'cir',
        'vasicek',
        'other',
    ]
    version: str
    approval_status: NotRequired[Literal[
        'draft',
        'pending_review',
        'approved',
        'deprecated',
    ]]
    approved_by: NotRequired[str | None]
    approved_at: NotRequired[str | None]
    attributes: NotRequired[dict[str, Any]]


class RegimeState(TypedDict):
    """Object kind ``regime_state`` — title field ``state_id``."""

    object_id: str
    kind: NotRequired[Literal['regime_state']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    target_urn: str
    detector: str
    state_id: str
    confidence: NotRequired[float | None]
    detected_at: str
    attributes: NotRequired[dict[str, Any]]


class RegulatoryNorm(TypedDict):
    """Object kind ``regulatory_norm`` — title field ``citation``."""

    object_id: str
    kind: NotRequired[Literal['regulatory_norm']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    citation: str
    effective_from: NotRequired[str | None]


class RiskLimit(TypedDict):
    """Object kind ``risk_limit`` — title field ``metric``."""

    object_id: str
    kind: NotRequired[Literal['risk_limit']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    metric: str
    threshold: float
    breach_action: NotRequired[Literal['alert', 'throttle', 'halt']]


class Scenario(TypedDict):
    """Object kind ``scenario`` — no title field."""

    rid: str
    kind: NotRequired[Literal['scenario']]
    name: str
    description: NotRequired[str]
    as_of: str
    overrides: NotRequired[list[Any]]
    hypothetical_links: NotRequired[list[Any]]
    type_edits: NotRequired[list[Any]]
    models: NotRequired[list[Any]]
    chain: NotRequired[dict[str, Any] | None]
    result_ref: NotRequired[str | None]
    created_by: str
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    created_at: str


class ScenarioDetection(TypedDict):
    """Object kind ``scenario_detection`` — title field ``scenario``."""

    object_id: str
    kind: NotRequired[Literal['scenario_detection']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    scenario: str
    confidence: float
    matched_signals: NotRequired[list[Any]]
    playbook_available: NotRequired[bool]
    as_of: str
    review: NotRequired[Literal['detected', 'confirmed', 'rejected']]
    reviewed_by: NotRequired[str | None]
    reviewed_at: NotRequired[str | None]
    review_note: NotRequired[str]
    attributes: NotRequired[dict[str, Any]]


class Sensor(TypedDict):
    """Object kind ``sensor`` — title field ``phenomenon``."""

    lat: NotRequired[float | None]
    lon: NotRequired[float | None]
    radius_km: NotRequired[float | None]
    object_id: str
    kind: NotRequired[Literal['sensor']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    phenomenon: str
    sensor_type: NotRequired[Literal[
        'satellite',
        'ground_station',
        'buoy',
        'api_feed',
        'social_signal',
        'registry',
        'other',
    ]]
    description: NotRequired[str | None]
    attributes: NotRequired[dict[str, Any]]


class SettlementInstruction(TypedDict):
    """Object kind ``settlement_instruction`` — title field ``instruction_id``."""

    object_id: str
    kind: NotRequired[Literal['settlement_instruction']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    instruction_id: str
    settlement_type: Literal[
        'off_chain_bilateral',
        'fireblocks_dvp',
        'atomic_onchain',
    ]
    status: Literal['pending', 'settling', 'settled', 'failed']
    asset_leg_state: Literal['pending', 'committed', 'failed']
    cash_leg_state: Literal['pending', 'committed', 'failed']
    account_id: str
    instrument: str
    notional_usd: float
    source: NotRequired[Literal['primary', 'secondary'] | None]
    adapter: NotRequired[str | None]
    settled_at: NotRequired[str | None]
    attributes: NotRequired[dict[str, Any]]


class StressScenario(TypedDict):
    """Object kind ``stress_scenario`` — title field ``scenario_key``."""

    object_id: str
    kind: NotRequired[Literal['stress_scenario']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    scenario_key: str


class StressTestResult(TypedDict):
    """Object kind ``stress_test_result`` — no title field."""

    object_id: str
    kind: NotRequired[Literal['stress_test_result']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    portfolio_urn: str
    scenario_urn: str
    pnl_value: NotRequired[float | None]
    pnl_pct: NotRequired[float | None]
    as_of: str
    currency: NotRequired[str]
    attributes: NotRequired[dict[str, Any]]


class Trade(TypedDict):
    """Object kind ``trade`` — no title field."""

    object_id: str
    kind: NotRequired[Literal['trade']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    trade_date: str
    settle_date: str
    notional: float
    side: Literal['buy', 'sell']


class TransformRun(TypedDict):
    """Object kind ``transform_run`` — title field ``transform_id``."""

    object_id: str
    kind: NotRequired[Literal['transform_run']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    transform_id: str
    snapshot_hash: NotRequired[str | None]
    spec_hash: str
    status: Literal['succeeded', 'quarantined', 'failed', 'skipped']
    started_at: str
    finished_at: NotRequired[str | None]
    rows_in: NotRequired[int]
    rows_out: NotRequired[int]
    error: NotRequired[str | None]
    checks: NotRequired[list[Any]]
    attributes: NotRequired[dict[str, Any]]


class VarReport(TypedDict):
    """Object kind ``var_report`` — no title field."""

    object_id: str
    kind: NotRequired[Literal['var_report']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    portfolio_urn: str
    method: Literal[
        'historical',
        'parametric',
        'monte_carlo',
        'evt_gpd',
        'evt_block_maxima',
    ]
    confidence: float
    horizon_days: int
    var_value: float
    es_value: NotRequired[float | None]
    as_of: str
    currency: NotRequired[str]
    tail_index_xi: NotRequired[float | None]
    tail_scale_sigma: NotRequired[float | None]
    tail_threshold: NotRequired[float | None]
    attributes: NotRequired[dict[str, Any]]


class VolSurface(TypedDict):
    """Object kind ``vol_surface`` — no title field."""

    object_id: str
    kind: NotRequired[Literal['vol_surface']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    underlying_urn: str
    snapshot_at: str
    surface: NotRequired[list[Any]]
    quote_source: NotRequired[str | None]
    attributes: NotRequired[dict[str, Any]]


class VolatilityEstimate(TypedDict):
    """Object kind ``volatility_estimate`` — no title field."""

    object_id: str
    kind: NotRequired[Literal['volatility_estimate']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    instrument_urn: str
    method: Literal[
        'realized_variance',
        'bipower_variation',
        'tsrv',
        'msrv',
        'realized_kernel',
        'garch_11',
        'gjr_garch',
        'egarch',
        'ewma',
        'har_rv',
        'har_rv_cj',
        'other',
    ]
    vol_kind: Literal['realized', 'forecast']
    vol_value: float
    annualized: NotRequired[bool]
    horizon_days: NotRequired[int | None]
    n_observations: NotRequired[int | None]
    jump_component: NotRequired[float | None]
    persistence: NotRequired[float | None]
    r_squared: NotRequired[float | None]
    log_likelihood: NotRequired[float | None]
    as_of: str
    attributes: NotRequired[dict[str, Any]]


class WikiPage(TypedDict):
    """Object kind ``wiki_page`` — title field ``title``."""

    object_id: str
    kind: NotRequired[Literal['wiki_page']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    title: str
    content: str
    as_of: str
    attributes: NotRequired[dict[str, Any]]


class YieldCurve(TypedDict):
    """Object kind ``yield_curve`` — no title field."""

    object_id: str
    kind: NotRequired[Literal['yield_curve']]
    created_at: NotRequired[str]
    marking: NotRequired[Literal['public', 'internal', 'confidential', 'restricted']]
    currency: str
    curve_kind: NotRequired[Literal['zero', 'par', 'swap', 'ois']]
    snapshot_at: str
    points: NotRequired[list[Any]]
    attributes: NotRequired[dict[str, Any]]


# --- Metadata as data ---

OBJECT_TYPES: dict[ObjectKind, type] = {
    'agent_verdict': AgentVerdict,
    'analysis_run': AnalysisRun,
    'backtest_result': BacktestResult,
    'case': Case,
    'check': Check,
    'check_report': CheckReport,
    'committee_pack': CommitteePack,
    'correlation_matrix': CorrelationMatrix,
    'counterparty': Counterparty,
    'credit_event_record': CreditEventRecord,
    'csa_margin_call': CsaMarginCall,
    'data_build': DataBuild,
    'data_job': DataJob,
    'data_schedule': DataSchedule,
    'data_source': DataSource,
    'decision': Decision,
    'execution_analytics': ExecutionAnalytics,
    'execution_quality_report': ExecutionQualityReport,
    'factor_model_fit': FactorModelFit,
    'geo_entity': GeoEntity,
    'greek_snapshot': GreekSnapshot,
    'hedge_program': HedgeProgram,
    'indicator': Indicator,
    'instrument': Instrument,
    'instrument_valuation': InstrumentValuation,
    'joint_scenario_sample': JointScenarioSample,
    'margin_requirement': MarginRequirement,
    'model_calibration': ModelCalibration,
    'observation': Observation,
    'operational_picture': OperationalPicture,
    'order_attestation': OrderAttestation,
    'otc_structured_trade': OtcStructuredTrade,
    'pe_fund': PeFund,
    'point_process_fit': PointProcessFit,
    'portfolio_company': PortfolioCompany,
    'portfolio_optimization': PortfolioOptimization,
    'position': Position,
    'pricing_model': PricingModel,
    'regime_state': RegimeState,
    'regulatory_norm': RegulatoryNorm,
    'risk_limit': RiskLimit,
    'scenario': Scenario,
    'scenario_detection': ScenarioDetection,
    'sensor': Sensor,
    'settlement_instruction': SettlementInstruction,
    'stress_scenario': StressScenario,
    'stress_test_result': StressTestResult,
    'trade': Trade,
    'transform_run': TransformRun,
    'var_report': VarReport,
    'vol_surface': VolSurface,
    'volatility_estimate': VolatilityEstimate,
    'wiki_page': WikiPage,
    'yield_curve': YieldCurve,
}

TITLE_FIELDS: dict[ObjectKind, str | None] = {
    'agent_verdict': 'topic',
    'analysis_run': 'label',
    'backtest_result': None,
    'case': 'title',
    'check': None,
    'check_report': None,
    'committee_pack': 'label',
    'correlation_matrix': None,
    'counterparty': 'legal_name',
    'credit_event_record': None,
    'csa_margin_call': None,
    'data_build': 'job_id',
    'data_job': 'job_id',
    'data_schedule': 'schedule_id',
    'data_source': 'name',
    'decision': 'label',
    'execution_analytics': None,
    'execution_quality_report': None,
    'factor_model_fit': None,
    'geo_entity': 'name',
    'greek_snapshot': None,
    'hedge_program': None,
    'indicator': 'indicator_key',
    'instrument': 'ticker',
    'instrument_valuation': None,
    'joint_scenario_sample': None,
    'margin_requirement': None,
    'model_calibration': None,
    'observation': 'phenomenon',
    'operational_picture': 'alert_level',
    'order_attestation': 'attestation_id',
    'otc_structured_trade': None,
    'pe_fund': 'name',
    'point_process_fit': None,
    'portfolio_company': 'name',
    'portfolio_optimization': None,
    'position': None,
    'pricing_model': None,
    'regime_state': 'state_id',
    'regulatory_norm': 'citation',
    'risk_limit': 'metric',
    'scenario': None,
    'scenario_detection': 'scenario',
    'sensor': 'phenomenon',
    'settlement_instruction': 'instruction_id',
    'stress_scenario': 'scenario_key',
    'stress_test_result': None,
    'trade': None,
    'transform_run': 'transform_id',
    'var_report': None,
    'vol_surface': None,
    'volatility_estimate': None,
    'wiki_page': 'title',
    'yield_curve': None,
}

#: Properties with a promoted column — filterable via /objects/search — per kind.
SEARCHABLE_PROPERTIES: dict[ObjectKind, dict[str, str]] = {
    'agent_verdict': {'agent_id': 'p_agent_id', 'topic': 'p_topic', 'as_of': 'p_as_of'},
    'analysis_run': {
        'label': 'p_run_label',
        'actor_id': 'p_actor',
        'status': 'p_run_status',
        'as_of': 'p_as_of',
    },
    'backtest_result': {'as_of': 'p_as_of'},
    'case': {'actor_id': 'p_actor'},
    'check': {},
    'check_report': {'status': 'p_check_status', 'intent': 'p_check_intent'},
    'committee_pack': {},
    'correlation_matrix': {},
    'counterparty': {'legal_name': 'p_legal_name', 'jurisdiction': 'p_jurisdiction'},
    'credit_event_record': {},
    'csa_margin_call': {},
    'data_build': {},
    'data_job': {},
    'data_schedule': {},
    'data_source': {},
    'decision': {},
    'execution_analytics': {'as_of': 'p_as_of'},
    'execution_quality_report': {'as_of': 'p_as_of'},
    'factor_model_fit': {'as_of': 'p_as_of'},
    'geo_entity': {},
    'greek_snapshot': {'as_of': 'p_as_of'},
    'hedge_program': {'as_of': 'p_as_of'},
    'indicator': {},
    'instrument': {'ticker': 'p_ticker', 'asset_class': 'p_asset_class', 'currency': 'p_currency'},
    'instrument_valuation': {'as_of': 'p_as_of'},
    'joint_scenario_sample': {},
    'margin_requirement': {'as_of': 'p_as_of'},
    'model_calibration': {},
    'observation': {
        'lat': 'p_lat',
        'lon': 'p_lon',
        'phenomenon': 'p_phenomenon',
        'observed_at': 'p_observed_at',
        'value': 'p_obs_value',
    },
    'operational_picture': {},
    'order_attestation': {},
    'otc_structured_trade': {'notional_usd': 'p_notional_usd', 'status': 'p_status'},
    'pe_fund': {},
    'point_process_fit': {'as_of': 'p_as_of'},
    'portfolio_company': {},
    'portfolio_optimization': {'as_of': 'p_as_of'},
    'position': {'notional': 'p_notional', 'quantity': 'p_quantity', 'as_of': 'p_as_of'},
    'pricing_model': {},
    'regime_state': {},
    'regulatory_norm': {},
    'risk_limit': {},
    'scenario': {},
    'scenario_detection': {},
    'sensor': {},
    'settlement_instruction': {
        'settlement_type': 'p_settlement_type',
        'status': 'p_status',
        'notional_usd': 'p_notional_usd',
    },
    'stress_scenario': {},
    'stress_test_result': {'as_of': 'p_as_of'},
    'trade': {},
    'transform_run': {},
    'var_report': {'as_of': 'p_as_of'},
    'vol_surface': {},
    'volatility_estimate': {'as_of': 'p_as_of'},
    'wiki_page': {},
    'yield_curve': {},
}


class LinkTypeSpec(TypedDict):
    """Declared signature of a link kind; ``None`` = unconstrained."""

    src_kind: str | None
    dst_kind: str | None
    cardinality: str | None


LINK_TYPES: dict[LinkKind, LinkTypeSpec] = {
    'backtested_on': {
        'src_kind': 'backtest_result',
        'dst_kind': 'position',
        'cardinality': 'many_to_many',
    },
    'belongs_to': {'src_kind': None, 'dst_kind': None, 'cardinality': None},
    'between': {'src_kind': None, 'dst_kind': None, 'cardinality': None},
    'calibrated_on': {'src_kind': None, 'dst_kind': None, 'cardinality': None},
    'cites': {'src_kind': 'agent_verdict', 'dst_kind': None, 'cardinality': 'many_to_many'},
    'compliant_with': {'src_kind': None, 'dst_kind': None, 'cardinality': None},
    'computed_for': {'src_kind': None, 'dst_kind': None, 'cardinality': 'many_to_many'},
    'constrained_by': {'src_kind': None, 'dst_kind': None, 'cardinality': None},
    'covers': {'src_kind': 'position', 'dst_kind': 'instrument', 'cardinality': 'one_to_one'},
    'decision_about': {'src_kind': 'decision', 'dst_kind': None, 'cardinality': 'many_to_many'},
    'derived_from': {'src_kind': None, 'dst_kind': None, 'cardinality': 'many_to_many'},
    'evidenced_by': {'src_kind': 'decision', 'dst_kind': 'analysis_run', 'cardinality': 'many_to_many'},
    'executed_for': {'src_kind': None, 'dst_kind': None, 'cardinality': None},
    'executed_via': {'src_kind': None, 'dst_kind': None, 'cardinality': None},
    'factor_loaded_on': {'src_kind': None, 'dst_kind': None, 'cardinality': None},
    'flow_observed_in': {'src_kind': None, 'dst_kind': None, 'cardinality': None},
    'has_underlying': {'src_kind': None, 'dst_kind': None, 'cardinality': None},
    'hedged_by': {'src_kind': None, 'dst_kind': None, 'cardinality': None},
    'held_by': {'src_kind': 'position', 'dst_kind': 'counterparty', 'cardinality': 'one_to_many'},
    'holds_portco': {
        'src_kind': 'pe_fund',
        'dst_kind': 'portfolio_company',
        'cardinality': 'many_to_many',
    },
    'influences': {'src_kind': 'indicator', 'dst_kind': 'instrument', 'cardinality': 'many_to_many'},
    'issued_by': {
        'src_kind': 'instrument',
        'dst_kind': 'counterparty',
        'cardinality': 'many_to_many',
    },
    'located_in': {'src_kind': 'geo_entity', 'dst_kind': 'geo_entity', 'cardinality': 'many_to_many'},
    'margin_required_for': {'src_kind': None, 'dst_kind': None, 'cardinality': None},
    'measures': {'src_kind': None, 'dst_kind': None, 'cardinality': None},
    'observed_by': {'src_kind': 'observation', 'dst_kind': 'sensor', 'cardinality': 'many_to_many'},
    'optimized_over': {'src_kind': None, 'dst_kind': None, 'cardinality': None},
    'priced_with': {'src_kind': None, 'dst_kind': None, 'cardinality': None},
    'produced': {'src_kind': 'analysis_run', 'dst_kind': None, 'cardinality': 'many_to_many'},
    'published_by': {'src_kind': 'sensor', 'dst_kind': 'data_source', 'cardinality': 'many_to_many'},
    'references': {'src_kind': 'wiki_page', 'dst_kind': None, 'cardinality': 'many_to_many'},
    'regime_classified': {'src_kind': None, 'dst_kind': None, 'cardinality': None},
    'sampled_with': {'src_kind': None, 'dst_kind': None, 'cardinality': None},
    'stressed_by': {'src_kind': None, 'dst_kind': None, 'cardinality': None},
    'uses_market_data': {'src_kind': 'model_calibration', 'dst_kind': None, 'cardinality': 'many_to_many'},
    'uses_model': {'src_kind': None, 'dst_kind': 'pricing_model', 'cardinality': 'many_to_many'},
    'valued_as': {
        'src_kind': 'instrument',
        'dst_kind': 'instrument_valuation',
        'cardinality': 'many_to_many',
    },
    'valued_with_model': {
        'src_kind': 'instrument_valuation',
        'dst_kind': 'pricing_model',
        'cardinality': 'many_to_many',
    },
    'verdict_about': {'src_kind': 'agent_verdict', 'dst_kind': None, 'cardinality': 'many_to_many'},
    'vol_estimated_for': {'src_kind': None, 'dst_kind': None, 'cardinality': None},
}


__all__ = [
    "LINK_KINDS",
    "LINK_TYPES",
    "LinkKind",
    "LinkTypeSpec",
    "OBJECT_KINDS",
    "OBJECT_TYPES",
    "ObjectKind",
    "SEARCHABLE_PROPERTIES",
    "TITLE_FIELDS",
    "AgentVerdict",
    "AnalysisRun",
    "BacktestResult",
    "Case",
    "Check",
    "CheckReport",
    "CommitteePack",
    "CorrelationMatrix",
    "Counterparty",
    "CreditEventRecord",
    "CsaMarginCall",
    "DataBuild",
    "DataJob",
    "DataSchedule",
    "DataSource",
    "Decision",
    "ExecutionAnalytics",
    "ExecutionQualityReport",
    "FactorModelFit",
    "GeoEntity",
    "GreekSnapshot",
    "HedgeProgram",
    "Indicator",
    "Instrument",
    "InstrumentValuation",
    "JointScenarioSample",
    "MarginRequirement",
    "ModelCalibration",
    "Observation",
    "OperationalPicture",
    "OrderAttestation",
    "OtcStructuredTrade",
    "PeFund",
    "PointProcessFit",
    "PortfolioCompany",
    "PortfolioOptimization",
    "Position",
    "PricingModel",
    "RegimeState",
    "RegulatoryNorm",
    "RiskLimit",
    "Scenario",
    "ScenarioDetection",
    "Sensor",
    "SettlementInstruction",
    "StressScenario",
    "StressTestResult",
    "Trade",
    "TransformRun",
    "VarReport",
    "VolSurface",
    "VolatilityEstimate",
    "WikiPage",
    "YieldCurve",
]
