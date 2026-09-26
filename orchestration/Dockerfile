# Scheduled dispatcher image.
# Places the day-keyed RunRequest from a Container Apps Job.
FROM dhi.io/python:3.13-dev AS build
WORKDIR /app
RUN python -m pip install --no-cache-dir "uv==0.4.29"
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --extra runtime --no-dev
COPY kernel/ kernel/
COPY contracts/ contracts/
COPY agents/__init__.py agents/__init__.py
COPY agents/analyst/__init__.py agents/analyst/__init__.py
COPY agents/analyst/history_requirements.py agents/analyst/history_requirements.py
COPY agents/analyst/settings.py agents/analyst/settings.py
COPY agents/analyst/settings_indicators.py agents/analyst/settings_indicators.py
COPY agents/analyst/settings_stop_target.py agents/analyst/settings_stop_target.py
COPY agents/portfolio_manager/__init__.py agents/portfolio_manager/__init__.py
COPY agents/portfolio_manager/agent.py agents/portfolio_manager/agent.py
COPY agents/portfolio_manager/domain/__init__.py agents/portfolio_manager/domain/__init__.py
COPY agents/portfolio_manager/domain/correlation.py agents/portfolio_manager/domain/correlation.py
COPY agents/portfolio_manager/domain/correlation_census.py agents/portfolio_manager/domain/correlation_census.py
COPY agents/portfolio_manager/domain/correlation_census_builder.py agents/portfolio_manager/domain/correlation_census_builder.py
COPY agents/portfolio_manager/domain/correlation_math.py agents/portfolio_manager/domain/correlation_math.py
COPY agents/portfolio_manager/domain/correlation_ramp.py agents/portfolio_manager/domain/correlation_ramp.py
COPY agents/portfolio_manager/domain/deployment_floor.py agents/portfolio_manager/domain/deployment_floor.py
COPY agents/portfolio_manager/domain/exits.py agents/portfolio_manager/domain/exits.py
COPY agents/portfolio_manager/domain/gate_report.py agents/portfolio_manager/domain/gate_report.py
COPY agents/portfolio_manager/domain/issuer.py agents/portfolio_manager/domain/issuer.py
COPY agents/portfolio_manager/domain/order_decision.py agents/portfolio_manager/domain/order_decision.py
COPY agents/portfolio_manager/domain/position_gates.py agents/portfolio_manager/domain/position_gates.py
COPY agents/portfolio_manager/domain/rejection_reasons.py agents/portfolio_manager/domain/rejection_reasons.py
COPY agents/portfolio_manager/domain/reward_risk_detail.py agents/portfolio_manager/domain/reward_risk_detail.py
COPY agents/portfolio_manager/domain/risk.py agents/portfolio_manager/domain/risk.py
COPY agents/portfolio_manager/domain/sector_book.py agents/portfolio_manager/domain/sector_book.py
COPY agents/portfolio_manager/domain/sector_gate_outcomes.py agents/portfolio_manager/domain/sector_gate_outcomes.py
COPY agents/portfolio_manager/domain/sizing.py agents/portfolio_manager/domain/sizing.py
COPY agents/portfolio_manager/domain/volatility.py agents/portfolio_manager/domain/volatility.py
COPY agents/portfolio_manager/graph_portfolio.py agents/portfolio_manager/graph_portfolio.py
COPY agents/portfolio_manager/issuer_map.py agents/portfolio_manager/issuer_map.py
COPY agents/portfolio_manager/market_context.py agents/portfolio_manager/market_context.py
COPY agents/portfolio_manager/portfolio.py agents/portfolio_manager/portfolio.py
COPY agents/portfolio_manager/provider_client.py agents/portfolio_manager/provider_client.py
COPY agents/portfolio_manager/pubsub.py agents/portfolio_manager/pubsub.py
COPY agents/portfolio_manager/result.py agents/portfolio_manager/result.py
COPY agents/portfolio_manager/run.py agents/portfolio_manager/run.py
COPY agents/portfolio_manager/settings.py agents/portfolio_manager/settings.py
COPY agents/portfolio_manager/store.py agents/portfolio_manager/store.py
COPY agents/provider/__init__.py agents/provider/__init__.py
COPY agents/provider/domain/__init__.py agents/provider/domain/__init__.py
COPY agents/provider/domain/market_calendar.py agents/provider/domain/market_calendar.py
COPY agents/provider/settings.py agents/provider/settings.py
COPY agents/provider/settings_feeds.py agents/provider/settings_feeds.py
COPY agents/scanner/__init__.py agents/scanner/__init__.py
COPY agents/scanner/settings.py agents/scanner/settings.py
COPY agents/scanner/universe.py agents/scanner/universe.py
COPY agents/supervisor/__init__.py agents/supervisor/__init__.py
COPY agents/supervisor/agent.py agents/supervisor/agent.py
COPY agents/supervisor/domain/__init__.py agents/supervisor/domain/__init__.py
COPY agents/supervisor/domain/gate.py agents/supervisor/domain/gate.py
COPY agents/supervisor/domain/hard_no.py agents/supervisor/domain/hard_no.py
COPY agents/supervisor/domain/health.py agents/supervisor/domain/health.py
COPY agents/supervisor/domain/matrix.py agents/supervisor/domain/matrix.py
COPY agents/supervisor/result.py agents/supervisor/result.py
COPY agents/supervisor/settings.py agents/supervisor/settings.py
COPY agents/supervisor/store.py agents/supervisor/store.py
COPY orchestration/__init__.py orchestration/__init__.py
COPY orchestration/batch_chain.py orchestration/batch_chain.py
COPY orchestration/batch_trace.py orchestration/batch_trace.py
COPY orchestration/daily_brief.py orchestration/daily_brief.py
COPY orchestration/daily_brief_facts.py orchestration/daily_brief_facts.py
COPY orchestration/daily_brief_fills.py orchestration/daily_brief_fills.py
COPY orchestration/daily_brief_guard.py orchestration/daily_brief_guard.py
COPY orchestration/daily_brief_text.py orchestration/daily_brief_text.py
COPY orchestration/fleet_readiness.py orchestration/fleet_readiness.py
COPY orchestration/history_window.py orchestration/history_window.py
COPY orchestration/hold_answers.py orchestration/hold_answers.py
COPY orchestration/observatory.py orchestration/observatory.py
COPY orchestration/packs/__init__.py orchestration/packs/__init__.py
COPY orchestration/packs/trading_acceptance.py orchestration/packs/trading_acceptance.py
COPY orchestration/packs/trading_boundaries.py orchestration/packs/trading_boundaries.py
COPY orchestration/packs/trading_deliberation_attribution.py orchestration/packs/trading_deliberation_attribution.py
COPY orchestration/packs/trading_deliberation_view.py orchestration/packs/trading_deliberation_view.py
COPY orchestration/packs/trading_fill_outcomes.py orchestration/packs/trading_fill_outcomes.py
COPY orchestration/packs/trading_observatory.py orchestration/packs/trading_observatory.py
COPY orchestration/packs/trading_observatory_chain.py orchestration/packs/trading_observatory_chain.py
COPY orchestration/packs/trading_observatory_views.py orchestration/packs/trading_observatory_views.py
COPY orchestration/packs/trading_run_postures.py orchestration/packs/trading_run_postures.py
COPY orchestration/packs/trading_run_postures.json orchestration/packs/trading_run_postures.json
COPY orchestration/packs/trading_stage_view.py orchestration/packs/trading_stage_view.py
COPY orchestration/packs/us_equities_sp500.py orchestration/packs/us_equities_sp500.py
COPY orchestration/pm_rejections.py orchestration/pm_rejections.py
COPY orchestration/scheduled_dispatch.py orchestration/scheduled_dispatch.py
COPY orchestration/scheduled_dispatch_actions.py orchestration/scheduled_dispatch_actions.py
COPY orchestration/scheduled_dispatch_gate.py orchestration/scheduled_dispatch_gate.py
COPY orchestration/scheduled_dispatch_human.py orchestration/scheduled_dispatch_human.py
COPY orchestration/scheduled_dispatch_polling.py orchestration/scheduled_dispatch_polling.py
COPY orchestration/settings.py orchestration/settings.py
COPY orchestration/start.py orchestration/start.py
COPY orchestration/telegram_client.py orchestration/telegram_client.py
COPY orchestration/telegram_http.py orchestration/telegram_http.py
COPY orchestration/telegram_port.py orchestration/telegram_port.py
COPY orchestration/telegram_updates.py orchestration/telegram_updates.py
COPY orchestration/trace_deliberation.py orchestration/trace_deliberation.py
COPY orchestration/trace_format.py orchestration/trace_format.py
COPY scripts/dispatch_scheduled_run.py scripts/dispatch_scheduled_run.py
COPY scripts/universe_sp100.txt scripts/universe_sp100.txt

FROM dhi.io/python:3.13
WORKDIR /app
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:${PATH}"
COPY --from=build /app /app
CMD ["python", "scripts/dispatch_scheduled_run.py"]
