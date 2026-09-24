import intake


def _hs(id_, lat, lon):
    return {"id": id_, "lat": lat, "lon": lon}


def test_cluster_hotspots_groups_nearby_points():
    # three points within ~200-400m of each other -> one cluster
    close = [_hs("a", 29.42, 79.43), _hs("b", 29.4205, 79.4305), _hs("c", 29.4195, 79.4295)]
    clusters = intake.cluster_hotspots(close, eps_km=1.0)
    assert len(clusters) == 1
    assert len(clusters[0]) == 3


def test_cluster_hotspots_separates_distant_points():
    far_apart = [_hs("a", 29.42, 79.43), _hs("b", 10.0, 10.0)]
    clusters = intake.cluster_hotspots(far_apart, eps_km=1.0)
    assert len(clusters) == 2


def test_cluster_hotspots_is_transitive():
    # a-b close, b-c close, a-c NOT close directly -> still one cluster via b
    chain = [_hs("a", 29.4200, 79.4300), _hs("b", 29.4290, 79.4300), _hs("c", 29.4380, 79.4300)]
    # a-b ~1km, b-c ~1km, a-c ~2km — eps=1.2km should chain them into one cluster
    clusters = intake.cluster_hotspots(chain, eps_km=1.2)
    assert len(clusters) == 1
    assert len(clusters[0]) == 3


def test_corroborate_confirms_clustered_points():
    close = [_hs("a", 29.42, 79.43), _hs("b", 29.4205, 79.4305), _hs("c", 29.4195, 79.4295)]
    result = intake.corroborate(close, eps_km=1.0, min_samples=2)
    assert len(result["confirmed"]) == 3
    assert len(result["unconfirmed"]) == 0
    assert result["cluster_count"] == 1


def test_corroborate_flags_isolated_single_point():
    isolated = [_hs("lone", 29.42, 79.43)]
    result = intake.corroborate(isolated, eps_km=1.0, min_samples=2)
    assert result["confirmed"] == []
    assert result["unconfirmed"] == isolated


def test_corroborate_mixed_clustered_and_isolated():
    pair = [_hs("a", 29.42, 79.43), _hs("b", 29.4205, 79.4305)]
    isolated = _hs("lone", 5.0, 5.0)
    result = intake.corroborate(pair + [isolated], eps_km=1.0, min_samples=2)
    assert len(result["confirmed"]) == 2
    assert result["unconfirmed"] == [isolated]


def test_corroborate_empty_input():
    result = intake.corroborate([], eps_km=1.0, min_samples=2)
    assert result == {"confirmed": [], "unconfirmed": [], "cluster_count": 0}
