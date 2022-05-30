/* misosoup/sql/get_ms1_features.sql

Get MS1 features and their neighborhood signals by msrun_id
*/

SELECT
    peak.peak_id
    ,peak.feature_id
    ,peak.peak_num
    ,peak.delta_mz
    ,peak.intensity AS peak_intensity
    ,peak.mz_group
    ,peak.xic_peak
    ,peak.frame AS peak_frame
    ,peak.rt AS peak_rt
    ,peak.spectrum AS peak_spectrum
    ,peak.tof AS peak_tof
    ,peak.mz AS peak_mz
    ,peak.ms1_id AS peak_center_ms1_id
    ,peak.n_signals AS peak_n_signals
    ,ms1.id
    ,frame.rt
    ,ms1.frame
    ,ms1.spectrum
    ,ms1.tof
    ,ms1.mz
    ,ms1.intensity
    ,peak.msrun_id
FROM peak
JOIN (
    SELECT DISTINCT feature_id, msrun_id
    FROM peak
    WHERE msrun_id IN {msrun_ids}
        {filter_clauses}
) feature
    ON feature.msrun_id = peak.msrun_id
    AND feature.feature_id = peak.feature_id
JOIN ms1
    ON ms1.msrun_id = peak.msrun_id
    AND ms1.mz_group = peak.mz_group
    AND ms1.spectrum - peak.spectrum BETWEEN -{spectrum_window}/2 AND {spectrum_window}/2
    AND ms1.tof - peak.tof BETWEEN -{tof_window} AND {tof_window}
    AND peak.intensity / ms1.intensity <= 500  -- signals contributing at least 0.01% to peak_intensity
JOIN frame
    ON frame.msrun_id = ms1.msrun_id
    AND frame.frame = ms1.frame
    AND frame.rt - peak.rt BETWEEN -{rt_window}/2 AND {rt_window}/2
WHERE ms1.intensity >= {min_ms1_intensity}

