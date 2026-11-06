'use client';
import { useState, useEffect, useCallback } from 'react';
import Image from 'next/image';

export default function Nav() {
    const [menuOpen, setMenuOpen] = useState(false);

    const closeMenu = useCallback(() => {
        setMenuOpen(false);
        document.body.style.overflow = '';
    }, []);

    const toggleMenu = useCallback(() => {
        setMenuOpen((prev) => {
            const next = !prev;
            document.body.style.overflow = next ? 'hidden' : '';
            return next;
        });
    }, []);

    useEffect(() => {
        function onOutside(e: MouseEvent) {
            const nav = document.getElementById('nav');
            if (nav && !nav.contains(e.target as Node)) closeMenu();
        }
        document.addEventListener('click', onOutside);
        return () => document.removeEventListener('click', onOutside);
    }, [closeMenu]);

    const links = [
        { href: '#process', label: 'Процесс' },
        { href: '#offer', label: 'Оценка' },
        { href: '#cases', label: 'Кейсы' },
        { href: '#cars', label: 'Авто' },
        { href: '#services', label: 'Услуги' },
        { href: '#about', label: 'О нас' },
    ];

    return (
        <nav id='nav'>
            <a href='#' className='nav-logo'>
                <Image src='/logo-mark.png' alt='Proday Auto 86' width={880} height={265} priority />
            </a>

            <ul className={`nav-links${menuOpen ? ' open' : ''}`} id='navLinks'>
                {links.map((l) => (
                    <li key={l.href}>
                        <a href={l.href} onClick={closeMenu}>
                            {l.label}
                        </a>
                    </li>
                ))}
            </ul>

            <a href='tel:+70000000000' className='nav-cta'>
                +7 (000) 000-00-00
            </a>

            <button
                className={`nav-burger${menuOpen ? ' open' : ''}`}
                id='navBurger'
                aria-label='Меню'
                onClick={toggleMenu}
            >
                <span />
                <span />
                <span />
            </button>
        </nav>
    );
}
