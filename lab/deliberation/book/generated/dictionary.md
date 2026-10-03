# Dictionary of the evidence packet (book Part I, generated from the code)

Every value below means what OUR code computes, not its textbook meaning.
Composite = weighted mean of present pillars {'technical': 0.5, 'fundamental': 0.3, 'sentiment': 0.2}; technical_score = 80% indicator mean + 20% rs_score; confidence = 0.3 + 0.6 x composite_score; buy floor = 0.6.

## composite
- `confidence_score` [fraction_0_1; higher_better]: The analyst's confidence = confidence_floor + confidence_span x composite_score. Gated against the regime's base_min_confidence_score. CAUTION: Not a probability of profit. It is a linear rescale of the composite score.
- `confidence` [fraction_0_1; higher_better; bookkeeping]: Same number as confidence_score, repeated inside quant_metrics.
- `composite_score` [fraction_0_1; higher_better]: Weighted mean of the pillars present: technical, fundamental, sentiment (weights in the house rules), renormalised over the pillars that exist. CAUTION: A missing pillar is dropped, not scored as zero: the composite can rest on technicals alone.

## technical
- `technical_score` [fraction_0_1; higher_better]: Mean of all indicator sub-scores (/100), then blended 80/20 with the relative-strength score. CAUTION: It AVERAGES contrarian sub-scores (RSI, Bollinger, stochastic, Williams, RSI-2, NW deviation) with trend sub-scores (SMA-200, EMA, MACD, golden cross, OBV). An extended leader and a falling knife can score within a few points of each other. Read the sub-scores, never this number alone.
- `rsi` [raw_indicator; contrarian_low_is_bullish]: 14-period Relative Strength Index, 0-100. Bands: x < 30 -> 80; x >= 30 and < 50 -> 65; x >= 50 and < 70 -> 50; x >= 70 -> 25. CAUTION: Scored contrarian: high RSI (overbought) gets a LOW sub-score.
- `rsi_score` [sub_score_0_100; higher_better]: Sub-score of rsi. Bands: x < 30 -> 80; x >= 30 and < 50 -> 65; x >= 50 and < 70 -> 50; x >= 70 -> 25. CAUTION: rsi_score=25 means rsi >= 70 (overbought), not weak momentum.
- `rsi2` [raw_indicator; contrarian_low_is_bullish]: 2-period RSI, 0-100: a very short-term overbought/oversold gauge. Bands: x < 10 -> 80; x >= 10 and <= 90 -> 50; x > 90 -> 20.
- `rsi2_score` [sub_score_0_100; higher_better]: Sub-score of rsi2 (contrarian). Bands: x < 10 -> 80; x >= 10 and <= 90 -> 50; x > 90 -> 20.
- `bollinger_position` [position_0_1; contrarian_low_is_bullish]: Where the close sits inside the Bollinger band: 0 = lower band, 1 = upper band. Bands: x < 0.3 -> 75; x >= 0.3 and < 0.7 -> 50; x >= 0.7 -> 30. CAUTION: Near the lower band is scored bullish (contrarian).
- `bollinger_position_score` [sub_score_0_100; higher_better]: Sub-score of bollinger_position. Bands: x < 0.3 -> 75; x >= 0.3 and < 0.7 -> 50; x >= 0.7 -> 30.
- `sma_distance_pct` [percent; higher_better]: Close's distance above (+) or below (-) its 200-day SMA, in %. Bands: x <= -5% -> 20; x > -5% and <= 0% -> 40; x > 0% and <= 5% -> 60; x > 5% -> 75. CAUTION: Trend-following: below the SMA-200 scores low.
- `sma_distance_pct_score` [sub_score_0_100; higher_better]: Sub-score of sma_distance_pct. Bands: x <= -5% -> 20; x > -5% and <= 0% -> 40; x > 0% and <= 5% -> 60; x > 5% -> 75.
- `ema_spread_pct` [percent; higher_better]: Short EMA minus long EMA as % of price (positive = up-trend). Bands: x <= -1% -> 25; x > -1% and <= 0% -> 40; x > 0% and <= 1% -> 60; x > 1% -> 75.
- `ema_spread_pct_score` [sub_score_0_100; higher_better]: Sub-score of ema_spread_pct. Bands: x <= -1% -> 25; x > -1% and <= 0% -> 40; x > 0% and <= 1% -> 60; x > 1% -> 75.
- `macd_histogram` [raw_indicator; higher_better]: MACD line minus signal line, in price units. Bands: line>0 and histogram>0 -> 75; histogram>0 only -> 60; line<0 and histogram<0 -> 25; otherwise -> 45. CAUTION: Its sub-score also depends on the sign of the MACD line, macd_line_price (absent from the production packet).
- `macd_histogram_score` [sub_score_0_100; higher_better]: Sub-score from MACD line and histogram signs. Bands: line>0 and histogram>0 -> 75; histogram>0 only -> 60; line<0 and histogram<0 -> 25; otherwise -> 45.
- `golden_cross` [flag_0_1; higher_better]: 1 when the 50-day SMA is above the 200-day SMA, else 0. Bands: golden cross -> 75; otherwise -> 25.
- `golden_cross_score` [sub_score_0_100; higher_better]: Sub-score of golden_cross. Bands: golden cross -> 75; otherwise -> 25.
- `obv` [raw_indicator; not_directional]: On-balance volume level (cumulative signed volume). Bands: OBV above its signal -> 70; otherwise -> 35. CAUTION: The level itself means nothing; only OBV vs its signal line is scored.
- `obv_score` [sub_score_0_100; higher_better]: 70 when OBV is above its signal average (accumulation), else 35. Bands: OBV above its signal -> 70; otherwise -> 35.
- `atr_pct` [percent; lower_better]: Average True Range as % of price: daily volatility. Bands: x < 2% -> 70; x >= 2% and < 4% -> 55; x >= 4% -> 35. CAUTION: Lower volatility scores higher. It also sizes the scaled stop.
- `atr_pct_score` [sub_score_0_100; higher_better]: Sub-score of atr_pct. Bands: x < 2% -> 70; x >= 2% and < 4% -> 55; x >= 4% -> 35.
- `stochastic_k` [raw_indicator; contrarian_low_is_bullish]: Stochastic %K, 0-100: close within the recent high-low range. Bands: %K and %D both < 20 -> 80; %K < 20 -> 65; %K and %D both > 80 -> 20; %K > 80 -> 35; otherwise 50. CAUTION: Scored with %D (stochastic_d; absent from the production packet): oversold high, overbought low.
- `stochastic_k_score` [sub_score_0_100; higher_better]: Sub-score from %K and %D. Bands: %K and %D both < 20 -> 80; %K < 20 -> 65; %K and %D both > 80 -> 20; %K > 80 -> 35; otherwise 50.
- `williams_r` [raw_indicator; contrarian_low_is_bullish]: Williams %R, -100..0 (-100 = at the period low). Bands: x < -80 -> 75; x >= -80 and <= -20 -> 50; x > -20 -> 25.
- `williams_r_score` [sub_score_0_100; higher_better]: Sub-score of williams_r (contrarian). Bands: x < -80 -> 75; x >= -80 and <= -20 -> 50; x > -20 -> 25.
- `choppiness` [raw_indicator; lower_better]: Choppiness index 0-100: low = trending, high = range-bound. Bands: x < 38.2 -> 75; x >= 38.2 and <= 61.8 -> 50; x > 61.8 -> 30.
- `choppiness_score` [sub_score_0_100; higher_better]: Sub-score of choppiness. Bands: x < 38.2 -> 75; x >= 38.2 and <= 61.8 -> 50; x > 61.8 -> 30.
- `nw_deviation_pct` [percent; contrarian_low_is_bullish]: Close's % deviation from a Nadaraya-Watson kernel-smoothed price line. Bands: x < -1% -> 70; x >= -1% and <= 1% -> 50; x > 1% -> 30. CAUTION: Below the smoothed line is scored bullish (contrarian).
- `nw_deviation_pct_score` [sub_score_0_100; higher_better]: Sub-score of nw_deviation_pct. Bands: x < -1% -> 70; x >= -1% and <= 1% -> 50; x > 1% -> 30.
- `turnaround` [flag_0_1; higher_better]: 1 when the turnaround pattern detector fires, else 0. Bands: signal -> 75; otherwise -> 50.
- `turnaround_score` [sub_score_0_100; higher_better]: 75 when turnaround fires, else neutral 50. Bands: signal -> 75; otherwise -> 50.
- `indicators_available` [count; not_directional; bookkeeping]: How many indicator sub-scores were averaged. CAUTION: Fewer indicators = a noisier technical_score.
- `history_bars` [count; higher_better; bookkeeping]: Daily bars the analyst had for this ticker. CAUTION: Below 200 the SMA-200 and golden cross cannot compute and are absent.

## fundamental
- `fundamental_score` [fraction_0_1; higher_better]: Mean of the fundamental sub-scores (pe, pb, roe, net_margin, current_ratio, debt_equity, eps_growth, revenue_growth) /100.
- `pe` [sub_score_0_100; higher_better]: SUB-SCORE of the trailing P/E ratio (cheaper scores higher). Bands: raw = peBasicExclExtraTTM or peTTM; first match wins: raw < 10 -> 80; raw <= 25 -> 60; otherwise -> 30 Non-positive raw values are skipped (no key). CAUTION: NOT the P/E ratio. The ratio is peBasicExclExtraTTM in the Fundamentals line. A loss-maker has no pe key at all.
- `pb` [sub_score_0_100; higher_better]: SUB-SCORE of price/book (cheaper scores higher). Bands: raw = pbQuarterly or pbAnnual; first match wins: raw < 1.5 -> 80; raw <= 3 -> 60; raw <= 5 -> 40; otherwise -> 20 Non-positive raw values are skipped (no key). CAUTION: NOT the ratio; raw value is pbQuarterly.
- `roe` [sub_score_0_100; higher_better]: SUB-SCORE of return on equity. Bands: raw = roeTTM; first match wins: raw > 15 -> 80; raw > 5 -> 55; otherwise -> 25. CAUTION: NOT the ratio; raw value is roeTTM (in %).
- `net_margin` [sub_score_0_100; higher_better]: SUB-SCORE of net profit margin. Bands: raw = netProfitMarginTTM; first match wins: raw > 20 -> 80; raw > 10 -> 55; otherwise -> 30. CAUTION: Raw value is netProfitMarginTTM (in %).
- `current_ratio` [sub_score_0_100; higher_better]: SUB-SCORE of the current ratio (liquidity). Bands: raw = currentRatioQuarterly; first match wins: raw > 1.5 -> 70; raw > 1 -> 50; otherwise -> 25 Non-positive raw values are skipped (no key). CAUTION: Raw value is currentRatioQuarterly.
- `debt_equity` [sub_score_0_100; higher_better]: SUB-SCORE of debt/equity (less debt scores higher). Bands: raw = totalDebt/totalEquityQuarterly or totalDebt/totalEquityAnnual; first match wins: raw < 0.5 -> 80; raw < 1 -> 65; raw < 2 -> 45; otherwise -> 20. CAUTION: A HIGH debt_equity sub-score means LOW leverage.
- `eps_growth` [sub_score_0_100; higher_better]: SUB-SCORE of trailing EPS growth year on year. Bands: raw = epsGrowthTTMYoy; first match wins: raw > 20 -> 85; raw > 5 -> 65; raw > -5 -> 45; otherwise -> 20. CAUTION: Raw value is epsGrowthTTMYoy (in %).
- `revenue_growth` [sub_score_0_100; higher_better]: SUB-SCORE of trailing revenue growth year on year. Bands: raw = revenueGrowthTTMYoy; first match wins: raw > 15 -> 80; raw > 5 -> 60; raw > -5 -> 45; otherwise -> 25. CAUTION: Raw value is revenueGrowthTTMYoy (in %).
- `fundamentals_available` [count; not_directional; bookkeeping]: How many fundamental sub-scores were averaged.
- `peBasicExclExtraTTM` [ratio; lower_better]: The actual trailing P/E ratio (vendor field).
- `pbQuarterly` [ratio; lower_better]: Price/book ratio (vendor).
- `roeTTM` [percent; higher_better]: Return on equity, % (vendor).
- `netProfitMarginTTM` [percent; higher_better]: Net profit margin, % (vendor).
- `currentRatioQuarterly` [ratio; higher_better]: Current assets / current liabilities (vendor).
- `totalDebt/totalEquityQuarterly` [ratio; lower_better]: Debt/equity ratio (vendor).
- `epsGrowthTTMYoy` [percent; higher_better]: EPS growth year on year, % (vendor).
- `revenueGrowthTTMYoy` [percent; higher_better]: Revenue growth year on year, % (vendor).

## sentiment
- `analyst_sentiment_score` [fraction_0_1; higher_better]: The analyst's news-headline sentiment pillar (0 all negative, 0.5 balanced, 1 all positive); 'n/a' when no headline contains a lexicon word. CAUTION: 'n/a' means no signal, not neutral, and the composite then rests on the other pillars.
- `sentiment_score` [fraction_0_1; higher_better]: Same lexicon pillar as analyst_sentiment_score, inside quant_metrics. Each headline scores 50+50*(pos-neg)/(pos+neg); headlines with no lexicon word are skipped. CAUTION: One strongly negative headline among few can pull the pillar to 0.
- `sentiment_articles` [count; not_directional; bookkeeping]: Number of HEADLINES that contained at least one lexicon word. CAUTION: Headlines, not articles read in full.
- `sentiment_batch_weighted_articles` [count; not_directional; bookkeeping]: Weighted headline denominator used by the mean (a headline shared across tickers weighs less).
- `sentiment_positive_words` [count; not_directional; bookkeeping]: Lexicon WORD occurrences counted as positive. CAUTION: Word counts, not article counts; they routinely exceed sentiment_articles (DL-112).
- `sentiment_negative_words` [count; not_directional; bookkeeping]: Lexicon WORD occurrences counted as negative. CAUTION: Word counts, not article counts (DL-112).
- `provider_sentiment_score` [provider_scale_undeclared; higher_better]: The data provider's own sentiment number for the ticker (scale not declared in our code). It does not feed the analyst's composite. CAUTION: A different scale and source from analyst_sentiment_score; do not compare the two numerically.

## relative_strength
- `relative_strength` [percentage_points; higher_better]: ANALYST: the stock's trailing return minus the benchmark's (SPY) over the same window, in percentage points. Bands: x <= -5 pp -> 20; x > -5 pp and <= 0 pp -> 40; x > 0 pp and <= 5 pp -> 60; x > 5 pp -> 80. CAUTION: The SCANNER's relative_strength is a different metric with the same name: the stock's own total return as a fraction (0.12 = +12 %), with no benchmark. Check which block the value is in.
- `rs_score` [sub_score_0_100; higher_better]: Sub-score of the analyst relative_strength; blended 20 % into technical_score. Bands: x <= -5 pp -> 20; x > -5 pp and <= 0 pp -> 40; x > 0 pp and <= 5 pp -> 60; x > 5 pp -> 80.

## risk
- `suggested_stop_pct` [percent; not_directional]: Analyst's protective stop distance below entry. CAUTION: In scaled mode it is a multiple of atr_pct.
- `suggested_target_pct` [percent; not_directional]: Analyst's profit target above entry. CAUTION: In scaled mode it is the trailing median 10-session favorable excursion (favorable_excursion_pct), which can be SMALLER than the stop.
- `applied_stop_pct` [percent; not_directional]: Stop actually applied (fleet mode = scaled).
- `applied_target_pct` [percent; not_directional]: Target actually applied.
- `favorable_excursion_pct` [fraction; higher_better]: Median best gain reached within favorable_excursion_horizon_days over the trailing windows (0.0266 = 2.66 %). CAUTION: A fraction here, while the stop/target lines show percent.
- `favorable_excursion_horizon_days` [days; not_directional; bookkeeping]: Horizon (sessions) of the excursion measure.
- `favorable_excursion_lookback_windows` [count; not_directional; bookkeeping]: Trailing windows sampled.
- `favorable_excursion_sample_count` [count; not_directional; bookkeeping]: Windows actually measured.
- `value_reward_risk_ratio` [ratio; higher_better]: target_pct / stop_pct for this order. CAUTION: The gate is DISCLOSURE_ONLY at threshold 0 on the fleet: a ratio below 1 still PASSES.
- `applied_reward_risk_ratio` [ratio; higher_better]: Reward/risk at the applied stop and target.
- `flat_stop_pct` [percent; not_directional]: Stop under the flat mode (the regime base stop).
- `flat_target_pct` [percent; not_directional]: Target under the flat mode.
- `scaled_stop_pct` [percent; not_directional]: Stop under the scaled mode: 2 x atr_pct on the fleet. CAUTION: The fleet runs scaled, so this is the applied stop.
- `scaled_target_pct` [percent; not_directional]: Target under the scaled mode: the trailing favorable excursion.
- `flat_reward_risk_ratio` [ratio; higher_better]: target/stop under the flat mode.
- `scaled_reward_risk_ratio` [ratio; higher_better]: target/stop under the scaled mode. CAUTION: Below 1 means the target is closer than the stop.
- `decision_atr_pct` [percent; lower_better]: ATR % the analyst had at decision time, carried on the order.

## scanner
- `scanner_score` [raw_indicator; higher_better]: The scanner's ranking score (equals its relative_strength feature).
- `rank_ordinal` [count; lower_better; bookkeeping]: Rank among scanner candidates (1 = strongest).
- `average_volume` [shares; higher_better]: Mean daily volume over the scanner window.
- `beta` [ratio; not_directional]: Beta vs the benchmark; >1 moves more than the market. CAUTION: Filtered at max_beta; matters more in risk-off regimes.
- `days_to_earnings` [days; higher_better]: Calendar days to the next earnings report. CAUTION: Names inside the earnings exclusion are already dropped; a value just above it means the report lands inside a 10-session hold.
- `latest_close` [usd; not_directional; bookkeeping]: Latest close used by the scanner.
- `universe_tickers` [count; not_directional; bookkeeping]: Size of the scanner's universe this run.
- `evaluated_tickers` [count; not_directional; bookkeeping]: Tickers the scanner evaluated.

## regime
- `label` [enum; not_directional]: Market regime label from the VIX (risk_on/neutral/risk_off/high/extreme).
- `vix_index` [index_points; lower_better]: CBOE VIX level the regime was classified on.
- `base_min_confidence_score` [fraction_0_1; not_directional]: Regime floor the analyst's confidence must clear.
- `base_stop_loss_pct` [percent; not_directional; bookkeeping]: Regime default stop (used when no analyst stop).
- `base_take_profit_pct` [percent; not_directional; bookkeeping]: Regime default target.
- `base_max_holding_days` [days; not_directional; bookkeeping]: Regime's intended maximum holding period, in sessions. CAUTION: Nothing in the fleet sells on this horizon today (work-queue 92).

## pm_gate
- `value_portfolio_ratio` [ratio; lower_better]: sizing: position value / portfolio value. CAUTION: Fleet cap is 1 % of the portfolio per name.
- `value_cluster_exposure_ratio` [ratio; lower_better]: correlated_cluster_pct: share of deployed capital in names correlated with this one. CAUTION: NOT-EVALUATED while deployment is below its floor: the gate did not look, it did not pass.
- `value_sector_exposure_ratio` [ratio; lower_better]: max_sector_pct: sector share of deployed capital. CAUTION: NOT-EVALUATED below the deployment floor.
- `value_sector_issuers` [count; lower_better]: max_names_per_sector: issuers in the sector incl. this one.
- `value_positions` [count; lower_better; bookkeeping]: max_positions: open issuers incl. this one.
- `value_order_cost_usd` [usd; not_directional; bookkeeping]: cash_available: this order's cost.
- `value_shares` [count; not_directional; bookkeeping]: min_order_quantity: whole shares ordered.
- `portfolio_value_usd` [usd; not_directional]: The account EQUITY the PM sizes against (cash + holdings). CAUTION: Equity, not cash: the PM's `cash` field carries equity in production.
- `deployed_portfolio_usd` [usd; not_directional]: Market value of current holdings: the denominator of the sector and cluster gates. CAUTION: Concentration is measured against DEPLOYED capital, not equity.
- `position_value_usd` [usd; not_directional; bookkeeping]: This order's value (sizing gate).
- `existing_issuer_value_usd` [usd; lower_better]: Value already held in this issuer.
- `existing_sector_issuers` [count; lower_better]: Issuers already held in this sector.
- `held_sector_value_usd` [usd; lower_better]: Value already held in this sector.
- `deployed_this_batch_usd` [usd; not_directional; bookkeeping]: Cost of other orders approved earlier in this batch, in this sector.
- `order_cost_usd` [usd; not_directional; bookkeeping]: This order's cost (sector gate).
- `cash_buffer_pct` [fraction; not_directional; bookkeeping]: Share of equity the PM keeps as cash (0.05 = 5 %).
- `reserved_cash_this_batch_usd` [usd; not_directional; bookkeeping]: Cash already reserved by earlier orders this batch.
- `deployment_pct` [fraction; not_directional]: Deployed capital / equity.
- `deployment_floor_pct` [fraction; not_directional]: Below this deployment the concentration gates do not evaluate. CAUTION: NOT-EVALUATED below the floor means the gate did not look.
- `cluster_value_usd` [usd; lower_better]: Order cost + this issuer's holding + each correlated holding x its ramp weight.
- `cluster_weight_total` [weight_sum; lower_better]: Sum of the ramp weights of held issuers correlated with this one.
- `examined_issuers` [count; not_directional; bookkeeping]: Held issuers the correlation gate compared with this one.
- `correlated_issuers` [compound; lower_better]: Each held issuer above the ramp start, as TICKER:correlation:wWEIGHT (daily-return correlation over the lookback; weight from the ramp). CAUTION: A correlation of 0.70 counts about half of that holding toward the cluster.
- `below_threshold_top` [compound; not_directional; bookkeeping]: The highest correlations that stayed below the ramp start, TICKER:correlation.
- `correlation_ramp` [compound; not_directional; bookkeeping]: Correlations at or below the first number count 0, at or above the second count fully, linear in between.
- `min_pair_overlap_bars` [count; higher_better; bookkeeping]: Fewest overlapping bars in any compared pair.
- `skipped_pairs` [count; lower_better; bookkeeping]: Pairs skipped for too little overlapping history.
- `threshold_portfolio_ratio` [ratio; not_directional; bookkeeping]: sizing cap: max position value / equity (fleet: 0.01).
- `threshold_shares` [count; not_directional; bookkeeping]: min_order_quantity threshold.
- `threshold_positions` [count; not_directional; bookkeeping]: max_positions threshold (fleet: 60).
- `threshold_available_cash_usd` [usd; not_directional; bookkeeping]: Cash available for this order after buffer and reservations. CAUTION: Rendered in scientific notation (7.441e+04 = 74,410).
- `threshold_reward_risk_ratio` [ratio; not_directional; bookkeeping]: reward_risk threshold (fleet: 0, disclosure only).
- `threshold_sector_exposure_ratio` [ratio; not_directional; bookkeeping]: max_sector_pct threshold (share of deployed capital).
- `threshold_sector_issuers` [count; not_directional; bookkeeping]: max_names_per_sector threshold.
- `threshold_cluster_exposure_ratio` [ratio; not_directional; bookkeeping]: max_correlated_cluster_pct threshold (share of deployed capital).

## order
- `quantity_shares` [count; not_directional; bookkeeping]: Shares the PM approved for this order.
- `est_price_usd` [usd; not_directional; bookkeeping]: Price the PM sized the order at (latest close).
- `stop_pct` [percent; not_directional]: The order's protective stop distance below entry. CAUTION: Rendered as PERCENT in the 'PM order' line (4.64%) and as a FRACTION in the reward_risk detail (0.0464).
- `target_pct` [percent; not_directional]: The order's profit target above entry. CAUTION: PERCENT in the 'PM order' line, FRACTION in the reward_risk detail.

## market_data
- `open_usd` [usd; not_directional; bookkeeping]: Latest daily bar: open.
- `high_usd` [usd; not_directional; bookkeeping]: Latest daily bar: high.
- `low_usd` [usd; not_directional; bookkeeping]: Latest daily bar: low.
- `close_usd` [usd; not_directional]: Latest daily bar: close.
- `volume_shares` [shares; higher_better; bookkeeping]: Latest daily bar: volume.

## data_quality
- `requested_tickers` [count; not_directional; bookkeeping]: Tickers the provider was asked for in this run.
- `returned_tickers` [count; higher_better; bookkeeping]: Tickers it returned; below requested means missing data.

## supplement
- `macd_line_price` [raw_indicator; higher_better]: MACD line (fast EMA - slow EMA), price units. CAUTION: Its sign decides macd_histogram_score together with the histogram.
- `macd_signal_price` [raw_indicator; not_directional]: MACD signal line; histogram = line - signal.
- `stochastic_d` [raw_indicator; contrarian_low_is_bullish]: Stochastic %D (smoothed %K); scored together with %K.
- `obv_signal` [raw_indicator; not_directional]: OBV signal line; OBV above it scores 70, below 35.
- `sma_N_usd` [usd; not_directional]: Simple moving average over the N days in the key (sma_50_usd, sma_200_usd). CAUTION: sma_50 above sma_200 is the golden cross; close vs sma_200 is sma_distance_pct.
- `ema_N_usd` [usd; not_directional]: Exponential moving average over the N days in the key (short and long). CAUTION: ema_spread_pct is the short-minus-long gap as % of price.
- `bollinger_middle_usd` [usd; not_directional]: Bollinger middle band (window SMA).
- `bollinger_upper_usd` [usd; not_directional]: Bollinger upper band (middle + sigma x std).
- `bollinger_lower_usd` [usd; not_directional]: Bollinger lower band (middle - sigma x std).
- `account_cash_usd` [usd; not_directional; bookkeeping]: Broker cash.
- `account_equity_usd` [usd; not_directional]: Broker equity (cash + holdings).
- `buying_power_usd` [usd; not_directional; bookkeeping]: Broker buying power.
- `deployed_usd` [usd; not_directional]: Market value of current holdings.
- `open_positions` [count; not_directional; bookkeeping]: Number of current holdings.
- `holding_TICKER_shares` [count; not_directional; bookkeeping]: Shares held in that ticker.
- `holding_TICKER_value_usd` [usd; not_directional]: Market value held in that ticker.

## forecast
- `barrier_p_stop_first` [fraction_0_1; lower_better; UNPROVEN]: Forecaster's probability that the stop is touched before the target within 10 sessions (GARCH(1,1)-t fitted on ~760 bars, 1,000 simulated paths). CAUTION: UNPROVEN: no live skill shown yet. Read it, weigh it, never decide on it alone (DEC-FORM-08).
- `barrier_p_target_first` [fraction_0_1; higher_better; UNPROVEN]: Probability the target is touched before the stop within 10 sessions. CAUTION: UNPROVEN, as above.
- `barrier_p_neither` [fraction_0_1; not_directional; UNPROVEN]: Probability neither is touched within 10 sessions. CAUTION: UNPROVEN, as above.
- `barrier_horizon_sessions` [days; not_directional; bookkeeping]: Horizon of the barrier forecast, in sessions.
- `barrier_history_bars` [count; higher_better; bookkeeping]: Bars the GARCH model was fitted on.
- `barrier_settled_claims` [count; higher_better]: Past barrier forecasts already settled against what happened; the forecast's skill cannot be judged before enough have settled.

