'use client';
import { FaPhone, FaTelegram, FaInstagram, FaVk, FaCommentDots } from 'react-icons/fa6';

export default function Footer() {
    return (
        <footer id='footer'>
            <div className='footer-inner'>
                <div className='footer-top'>
                    {/* Brand */}
                    <div className='footer-brand'>
                        <p className='footer-tagline'>
                            Выкуп автомобилей в любом состоянии – до 90%
                            рыночной стоимости. Работаем 24/7 в Сургуте, ХМАО и
                            ЯНАО.
                        </p>
                    </div>

                    {/* Контакты */}
                    <div className='footer-col'>
                        <div className='footer-col-title'>Контакты</div>
                        <ul>
                            <li>
                                <a href='tel:+70000000000'>
                                    <span className='fc-dot' />
                                    +7 (000) 000-00-00
                                </a>
                            </li>
                            <li>
                                <a
                                    href='https://t.me/your_channel'
                                    target='_blank'
                                    rel='noopener noreferrer'
                                >
                                    <span className='fc-dot' />
                                    Telegram-канал
                                </a>
                            </li>
                            <li>
                                <a
                                    href='https://www.instagram.com/your_account'
                                    target='_blank'
                                    rel='noopener noreferrer'
                                >
                                    <span className='fc-dot' />
                                    Instagram
                                </a>
                            </li>
                            <li>
                                <a href='#about'>
                                    <span className='fc-dot' />
                                    Сургут, ХМАО
                                </a>
                            </li>
                        </ul>
                    </div>
                </div>

                {/* Bottom */}
                <div className='footer-bottom'>
                    <div className='footer-bottom-right'>
                        <div className='footer-socials'>
                            <a href='tel:+70000000000' aria-label='Позвонить'>
                                <FaPhone size={15} />
                            </a>
                            <a
                                href='https://t.me/your_channel'
                                target='_blank'
                                rel='noopener noreferrer'
                                aria-label='Telegram'
                            >
                                <FaTelegram size={17} />
                            </a>
                            <a
                                href='https://www.instagram.com/your_account'
                                target='_blank'
                                rel='noopener noreferrer'
                                aria-label='Instagram'
                            >
                                <FaInstagram size={17} />
                            </a>
                            <a
                                href='https://vk.com/your_group'
                                target='_blank'
                                rel='noopener noreferrer'
                                aria-label='VK'
                            >
                                <FaVk size={17} />
                            </a>
                            <a
                                href='https://max.ru/join/your_group'
                                target='_blank'
                                rel='noopener noreferrer'
                                aria-label='MAX'
                            >
                                <FaCommentDots size={17} />
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </footer>
    );
}
