import { useRatesStream } from '../../hooks/useRatesStream';
import type { PairState } from '../../types/rates';
import { MiniChart } from '../../components/MiniChart/MiniChart';
import './Dashboard.scss';

export function Dashboard() {
  const { rates, connectionStatus, error } = useRatesStream();

  const rateList: PairState[] = rates ?? [];

  return (
    <div className="dashboard">
      <header className="dashboard__header">
        <div>
          <h1 className="dashboard__title">Crypto Streaming Dashboard</h1>
          <p className="dashboard__subtitle">Live ETH pairs from your FastAPI backend</p>
        </div>

        <div className={`dashboard__status dashboard__status--${connectionStatus}`}>
          <span className="dashboard__status-dot" />
          <span className="dashboard__status-text">{connectionStatus}</span>
        </div>
      </header>

      {error && <p className="dashboard__error">{error}</p>}

      <main className="dashboard__content">
        <div className="dashboard__grid">
          {rateList.map((rate: PairState) => (
            <div className="rate-card" key={rate.pair}>
              <h2 className="rate-card__title">{rate.pair}</h2>

              {/* Tiny live chart based on recent prices */}
              <div className="rate-card__chart">
                <MiniChart points={rate.history} />
              </div>

              <div className="rate-card__row">
                <span className="rate-card__label">Current price</span>
                <span className="rate-card__value">
                  {rate.price !== null && rate.price !== undefined ? rate.price.toFixed(2) : '--'}
                </span>
              </div>

              <div className="rate-card__row">
                <span className="rate-card__label">Hourly average</span>
                <span className="rate-card__value">
                  {rate.hourly_avg !== null && rate.hourly_avg !== undefined
                    ? rate.hourly_avg.toFixed(2)
                    : '--'}
                </span>
              </div>

              <div className="rate-card__row">
                <span className="rate-card__label">Last update</span>
                <span className="rate-card__value rate-card__value--muted">
                  {rate.last_update ? new Date(rate.last_update).toLocaleString() : '--'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
