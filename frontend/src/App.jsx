import { useMemo, useState } from 'react'

const TAB_DEFS = [
  { id: 'products', label: 'Produits' },
  { id: 'services', label: 'Services' },
  { id: 'vendors', label: 'Boutiques' },
  { id: 'providers', label: 'Prestataires' },
]

function formatPrice(n) {
  if (n == null || Number.isNaN(n)) return '—'
  return `${Math.round(n).toLocaleString('fr-FR')} FCFA`
}

function ProductCard({ item }) {
  const hasPromo = item.discountPct != null && item.discountPct > 0 && item.oldPrice != null
  return (
    <a href={item.url} className="react-card react-card--product">
      {item.image ? <img src={item.image} alt="" /> : <div className="react-card__placeholder" />}
      <div>
        <h4>{item.name}</h4>
        {item.kind === 'service' ? <span className="react-card__kind">Service</span> : null}
        {hasPromo ? (
          <p className="react-card__price-row">
            <span className="react-card__price-old">{formatPrice(item.oldPrice)}</span>
            <span className="react-card__price-now">{formatPrice(item.price)}</span>
            <span className="react-card__pct">-{item.discountPct} %</span>
          </p>
        ) : (
          <p className="react-card__price-single">{formatPrice(item.price)}</p>
        )}
      </div>
    </a>
  )
}

function EntityCard({ item, subtitle }) {
  return (
    <a href={item.url} className="react-card react-card--entity">
      {item.image ? <img src={item.image} alt="" /> : <div className="react-card__placeholder" />}
      <div>
        <h4>{item.name}</h4>
        {subtitle ? <p className="react-card__sub">{subtitle}</p> : null}
      </div>
    </a>
  )
}

function App({ data }) {
  const {
    title,
    subtitle,
    highlights = [],
    products = [],
    discoverTabs = {},
    discoverMoreUrls = {},
  } = data || {}

  const [tab, setTab] = useState('products')

  const tabItems = useMemo(() => {
    const map = {
      products: discoverTabs.products || [],
      services: discoverTabs.services || [],
      vendors: discoverTabs.vendors || [],
      providers: discoverTabs.providers || [],
    }
    return map[tab] || []
  }, [tab, discoverTabs])

  const moreUrl = discoverMoreUrls[tab] || '#'

  return (
    <div className="react-hero">
      <div className="react-hero__text">
        <span className="react-hero__badge">Marketplace locale</span>
        <h2>{title || 'Découvrez les artisans près de chez vous'}</h2>
        <p>{subtitle || 'Achetez et réservez des services en toute confiance.'}</p>
        <div className="react-hero__highlights">
          {highlights.map((item) => (
            <div key={item.title} className="react-hero__highlight">
              <strong>{item.title}</strong>
              <span>{item.subtitle}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="react-discover">
        <div className="react-discover__head">
          <h3 className="react-discover__title">À découvrir</h3>
          <a className="react-discover__more" href={moreUrl}>
            Tout voir →
          </a>
        </div>
        <div className="react-discover__tabs" role="tablist" aria-label="Explorer la marketplace">
          {TAB_DEFS.map((t) => (
            <button
              key={t.id}
              type="button"
              role="tab"
              aria-selected={tab === t.id}
              className={tab === t.id ? 'react-tab react-tab--active' : 'react-tab'}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>
        <div className="react-discover__grid" role="tabpanel">
          {tab === 'products' || tab === 'services'
            ? tabItems.map((item) => <ProductCard key={`${tab}-${item.id}`} item={item} />)
            : tabItems.map((item) => (
                <EntityCard
                  key={`${tab}-${item.id}`}
                  item={item}
                  subtitle={tab === 'providers' ? item.location : ''}
                />
              ))}
        </div>
        {tabItems.length === 0 ? (
          <p className="react-discover__empty">Aucun élément dans cette rubrique pour le moment.</p>
        ) : null}
      </div>

      <div className="react-hero__grid react-hero__grid--mini">
        <p className="react-hero__mini-label">Sélection du moment</p>
        {products.slice(0, 4).map((product) => (
          <ProductCard key={product.id} item={product} />
        ))}
      </div>
    </div>
  )
}

export default App
