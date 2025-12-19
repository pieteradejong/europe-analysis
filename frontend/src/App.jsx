import { useState, useEffect } from "react";
import "./App.css";

const API_BASE = "http://localhost:8000";

function App() {
  const [stats, setStats] = useState(null);
  const [regions, setRegions] = useState([]);
  const [demographics, setDemographics] = useState([]);
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedRegion, setSelectedRegion] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  // Fetch initial data
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        const [statsRes, regionsRes, sourcesRes] = await Promise.all([
          fetch(`${API_BASE}/api/data/stats`),
          fetch(`${API_BASE}/api/data/regions`),
          fetch(`${API_BASE}/api/data/sources`),
        ]);

        if (!statsRes.ok || !regionsRes.ok || !sourcesRes.ok) {
          throw new Error("Failed to fetch data from API");
        }

        const [statsData, regionsData, sourcesData] = await Promise.all([
          statsRes.json(),
          regionsRes.json(),
          sourcesRes.json(),
        ]);

        setStats(statsData);
        setRegions(regionsData.regions || []);
        setSources(sourcesData.sources || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Fetch demographics when region changes
  useEffect(() => {
    if (!selectedRegion) {
      setDemographics([]);
      return;
    }

    const fetchDemographics = async () => {
      try {
        const res = await fetch(
          `${API_BASE}/api/data/demographics?region_code=${selectedRegion}&limit=100`
        );
        if (res.ok) {
          const data = await res.json();
          setDemographics(data.data || []);
        }
      } catch (err) {
        console.error("Failed to fetch demographics:", err);
      }
    };

    fetchDemographics();
  }, [selectedRegion]);

  // Filter regions by search query
  const filteredRegions = regions.filter(
    (r) =>
      r.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.code?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="app">
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading European Demographics Data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="app">
        <div className="error-container">
          <h1>⚠️ Connection Error</h1>
          <p>{error}</p>
          <p className="hint">
            Make sure the backend is running at {API_BASE}
          </p>
          <button onClick={() => window.location.reload()}>Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="header">
        <h1>🇪🇺 Europe Demographics Analysis</h1>
        <p className="subtitle">Explore population data across European regions</p>
      </header>

      {/* Statistics Overview */}
      <section className="stats-grid">
        <div className="stat-card">
          <span className="stat-icon">📊</span>
          <div className="stat-content">
            <span className="stat-value">{stats?.total_sources || 0}</span>
            <span className="stat-label">Data Sources</span>
          </div>
        </div>
        <div className="stat-card">
          <span className="stat-icon">🗺️</span>
          <div className="stat-content">
            <span className="stat-value">{stats?.total_regions || 0}</span>
            <span className="stat-label">Regions</span>
          </div>
        </div>
        <div className="stat-card">
          <span className="stat-icon">👥</span>
          <div className="stat-content">
            <span className="stat-value">
              {stats?.demographics?.total_records?.toLocaleString() || 0}
            </span>
            <span className="stat-label">Data Points</span>
          </div>
        </div>
        <div className="stat-card">
          <span className="stat-icon">📅</span>
          <div className="stat-content">
            <span className="stat-value">
              {stats?.demographics?.years_covered || "N/A"}
            </span>
            <span className="stat-label">Years Covered</span>
          </div>
        </div>
      </section>

      {/* Main Content */}
      <div className="main-content">
        {/* Regions Panel */}
        <section className="panel regions-panel">
          <h2>🗺️ Regions</h2>
          <input
            type="search"
            placeholder="Search regions..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
          <div className="regions-list">
            {filteredRegions.length === 0 ? (
              <p className="empty-state">
                {regions.length === 0
                  ? "No regions available. Import data to get started."
                  : "No regions match your search."}
              </p>
            ) : (
              filteredRegions.slice(0, 50).map((region) => (
                <button
                  key={region.id}
                  className={`region-item ${
                    selectedRegion === region.code ? "selected" : ""
                  }`}
                  onClick={() => setSelectedRegion(region.code)}
                >
                  <span className="region-code">{region.code}</span>
                  <span className="region-name">{region.name}</span>
                  {region.level && (
                    <span className="region-level">Level {region.level}</span>
                  )}
                </button>
              ))
            )}
            {filteredRegions.length > 50 && (
              <p className="more-hint">
                +{filteredRegions.length - 50} more regions
              </p>
            )}
          </div>
        </section>

        {/* Demographics Panel */}
        <section className="panel demographics-panel">
          <h2>👥 Demographics</h2>
          {selectedRegion ? (
            demographics.length > 0 ? (
              <div className="demographics-table-container">
                <table className="demographics-table">
                  <thead>
                    <tr>
                      <th>Year</th>
                      <th>Age Range</th>
                      <th>Gender</th>
                      <th>Population</th>
                    </tr>
                  </thead>
                  <tbody>
                    {demographics.map((d) => (
                      <tr key={d.id}>
                        <td>{d.year}</td>
                        <td>
                          {d.age_min !== null && d.age_max !== null
                            ? `${d.age_min}-${d.age_max}`
                            : "All ages"}
                        </td>
                        <td>{d.gender || "Total"}</td>
                        <td>{d.population?.toLocaleString() || "N/A"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="empty-state">
                No demographic data available for this region.
              </p>
            )
          ) : (
            <p className="empty-state">
              Select a region to view demographic data.
            </p>
          )}
        </section>
      </div>

      {/* Data Sources */}
      <section className="panel sources-panel">
        <h2>📁 Data Sources</h2>
        {sources.length === 0 ? (
          <p className="empty-state">
            No data sources configured. Use the API to acquire data.
          </p>
        ) : (
          <div className="sources-grid">
            {sources.map((source) => (
              <div key={source.id} className="source-card">
                <h3>{source.name}</h3>
                <span className="source-type">{source.type}</span>
                {source.last_updated && (
                  <span className="source-updated">
                    Updated: {new Date(source.last_updated).toLocaleDateString()}
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      <footer className="footer">
        <p>
          Europe Demographics Analysis • Backend API:{" "}
          <a href={`${API_BASE}/docs`} target="_blank" rel="noopener noreferrer">
            {API_BASE}/docs
          </a>
        </p>
      </footer>
    </div>
  );
}

export default App;
