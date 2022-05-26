/* misosoup/duckdb/get_chromatograms.sql

Get chromatogram (frame-by-frame overview) by msrun_id

*/

SELECT
    f.rt,
    f.tic,
    f.top_intensity AS bpc,
    f.num_signals,
    f.msrun_id
FROM frame f
WHERE 1=1
    AND f.ms_level = {ms_level}
ORDER BY msrun_id, rt
