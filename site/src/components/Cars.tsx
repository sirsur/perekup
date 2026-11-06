import { FiShield } from 'react-icons/fi'

const TYPES = [
    { name: 'Легковые', desc: 'Седаны, хэтчбеки, кроссоверы' },
    { name: 'Коммерческие', desc: 'Такси, каршеринг, парк компаний' },
    { name: 'Грузовые', desc: 'Малотоннажные и коммерческие' },
    { name: 'Премиум', desc: 'От 2 млн ₽ и выше' },
]

const BRANDS = [
    'Toyota', 'BMW', 'Mercedes-Benz', 'KIA', 'Hyundai', 'Lada',
    'Audi', 'Volkswagen', 'Nissan', 'Renault', 'Skoda', 'Chery',
]

export default function Cars() {
    return (
        <section id='cars'>
            <div className='bento-head reveal'>
                <div>
                    <h2 className='s-title'>
                        Какие авто
                        <br />
                        <em>покупаем</em>
                    </h2>
                </div>
            </div>

            <div className='cars-stat-row reveal'>
                <div className='cars-stat-block'>
                    <div className='cars-stat-num'>до 90%</div>
                    <div className='cars-stat-label'>Рыночной стоимости</div>
                </div>
                <div className='cars-stat-statement'>
                    <FiShield size={26} />
                    <p>
                        После ДТП, не на ходу, без документов, кредитные –
                        принимаем без отказа
                    </p>
                </div>
            </div>

            <div className='cars-types-row'>
                {TYPES.map((t, i) => (
                    <div
                        className='cars-type reveal'
                        key={t.name}
                        style={{ transitionDelay: i * 0.08 + 's' }}
                    >
                        <div className='cars-type-name'>{t.name}</div>
                        <div className='cars-type-desc'>{t.desc}</div>
                    </div>
                ))}
            </div>

            <div className='cars-brands-row reveal'>
                <p className='cars-brands-label'>Принимаем все марки и модели</p>
                <div className='cars-brands-list'>
                    {BRANDS.map((b) => (
                        <span className='cars-brand' key={b}>
                            {b}
                        </span>
                    ))}
                </div>
            </div>
        </section>
    )
}
