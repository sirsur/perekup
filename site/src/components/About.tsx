export default function About() {
    return (
        <section id='about'>
            <div className='ab-inner'>
                <div className='ab-left reveal'>
                    <h2 className='ab-title'>
                        Выкупаем
                        <br />
                        авто <em>быстро</em>
                        <br />и выгодно
                    </h2>
                    <p className='ab-desc'>
                        Автовыкуп ХМАО ЯНАО – профессиональный сервис в Сургуте
                        и по всему округу. Принимаем любые авто: аварийные,
                        кредитные, без документов, не на ходу. Расчёт наличными
                        в день обращения по официальному договору.
                    </p>
                    <a href='#offer' className='ab-btn'>
                        Оставить заявку
                        <svg
                            width='15'
                            height='15'
                            viewBox='0 0 24 24'
                            fill='none'
                            stroke='currentColor'
                            strokeWidth='2.2'
                            strokeLinecap='round'
                            strokeLinejoin='round'
                        >
                            <path d='M5 12h14M12 5l7 7-7 7' />
                        </svg>
                    </a>
                </div>

                <div
                    className='ab-stats reveal'
                    style={{ transitionDelay: '0.18s' }}
                >
                    {[
                        {
                            num: '500',
                            suffix: '+',
                            label: 'Выкуплено авто',
                            desc: 'Каждый автомобиль – честная сделка по рыночной цене',
                        },
                        {
                            num: '90',
                            suffix: '%',
                            label: 'Рыночной стоимости',
                            desc: 'Справедливая оценка без занижений и скрытых вычетов',
                        },
                        {
                            num: '10',
                            suffix: '+',
                            label: 'Лет на рынке',
                            desc: 'Профессиональный опыт в каждой сделке, без лишних вопросов',
                        },
                        {
                            num: '24',
                            suffix: '/7',
                            label: 'Приём заявок',
                            desc: 'Работаем без выходных по всему ХМАО-ЯНАО',
                        },
                    ].map((s) => (
                        <div className='ab-stat' key={s.label}>
                            <div className='ab-stat-num'>
                                {s.num}
                                <span>{s.suffix}</span>
                            </div>
                            <div className='ab-stat-label'>{s.label}</div>
                            <div className='ab-stat-desc'>{s.desc}</div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}
