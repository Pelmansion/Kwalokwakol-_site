function App({ data }) {
  const { title, subtitle, highlights = [], products = [] } = data || {}

  return (
    <div className="react-hero">
      <div className="react-hero__text">
        <span className="react-hero__badge">Marketplace local</span>
        <h2>{title || 'Découvrez les artisans près de chez vous'}</h2>
        <p>{subtitle || "Achetez et réservez des services en toute confiance."}</p>
        <div className="react-hero__highlights">
          {highlights.map((item) => (
            <div key={item.title} className="react-hero__highlight">
              <strong>{item.title}</strong>
              <span>{item.subtitle}</span>
            </div>
          ))}
        </div>
      </div>
      <div className="react-hero__grid">
        {products.slice(0, 4).map((product) => (
          <a key={product.id} href={product.url} className="react-card">
            {product.image ? (
              <img src={product.image} alt={product.name} />
            ) : (
              <div className="react-card__placeholder" />
            )}
            <div>
              <h4>{product.name}</h4>
              <p>{product.price} FCFA</p>
            </div>
          </a>
        ))}
      </div>
    </div>
  )
}

export default App
