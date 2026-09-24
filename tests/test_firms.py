import os

import firms


SAMPLE_CSV = (
    "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,"
    "confidence,version,bright_ti5,frp,daynight\n"
    "29.4187,79.4310,320.5,0.4,0.4,2026-04-15,0630,N,nominal,2.0NRT,290.1,18.4,D\n"
    "29.4201,79.4338,335.2,0.4,0.4,2026-04-15,0630,N,high,2.0NRT,295.0,27.1,D\n"
)

MALFORMED_ROW_CSV = SAMPLE_CSV + "not,a,valid,row,,,,,,,,,\n"


def test_parse_firms_csv_basic():
    hotspots = firms.parse_firms_csv(SAMPLE_CSV)
    assert len(hotspots) == 2
    assert hotspots[0]["lat"] == 29.4187
    assert hotspots[0]["lon"] == 79.4310
    assert hotspots[0]["confidence"] == "nominal"
    assert hotspots[0]["frp_mw"] == 18.4
    assert hotspots[1]["confidence"] == "high"


def test_parse_firms_csv_skips_malformed_rows():
    hotspots = firms.parse_firms_csv(MALFORMED_ROW_CSV)
    assert len(hotspots) == 2  # the trailing garbage row is dropped, not raised


def test_fetch_live_hotspots_returns_none_without_map_key(monkeypatch):
    monkeypatch.delenv("AGNIMARG_FIRMS_MAP_KEY", raising=False)
    result = firms.fetch_live_hotspots(29.32, 79.40, 29.44, 79.52)
    assert result is None
