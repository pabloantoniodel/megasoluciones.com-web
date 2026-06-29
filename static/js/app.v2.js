// Mobile Menu Toggle
document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuToggle = document.getElementById('mobileMenuToggle');
    const navLinks = document.getElementById('navLinks');
    
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', function() {
            navLinks.classList.toggle('active');
            this.classList.toggle('active');
        });
    }
    
    // Close flash messages
    const closeButtons = document.querySelectorAll('.close-alert');
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            this.parentElement.style.animation = 'slideInRight 0.3s ease reverse';
            setTimeout(() => {
                this.parentElement.remove();
            }, 300);
        });
    });
    
    // Auto-hide flash messages after 5 seconds
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            alert.style.animation = 'slideInRight 0.3s ease reverse';
            setTimeout(() => {
                alert.remove();
            }, 300);
        });
    }, 5000);

    // Aviso traducción EN (accesibilidad)
    const i18nToast = document.getElementById('i18nToastOverlay');
    if (i18nToast) {
        const closeToast = () => i18nToast.remove();
        i18nToast.querySelectorAll('.close-i18n-toast').forEach(btn => {
            btn.addEventListener('click', closeToast);
        });
        i18nToast.addEventListener('click', (e) => {
            if (e.target === i18nToast) closeToast();
        });
    }
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Navbar background on scroll
    const navbar = document.querySelector('.navbar');
    const isHomeNavbar = navbar && navbar.classList.contains('navbar-home');
    const navbarBgDefault = isHomeNavbar ? '#f9fbfa' : 'rgba(255, 255, 255, 0.95)';
    const navbarBgScrolled = isHomeNavbar ? '#f9fbfa' : 'rgba(255, 255, 255, 0.98)';
    
    window.addEventListener('scroll', () => {
        if (!navbar) return;
        const currentScroll = window.pageYOffset;
        
        if (currentScroll > 100) {
            navbar.style.background = navbarBgScrolled;
            navbar.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.1)';
        } else {
            navbar.style.background = navbarBgDefault;
            navbar.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1)';
        }
    });
    
    // Intersection Observer for fade-in animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observe service cards, testimonials, etc.
    const animatedElements = document.querySelectorAll(
        '.service-card, .testimonial-card, .portfolio-card, .feature-item, .process-step, .value-card'
    );
    
    animatedElements.forEach((el, index) => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = `all 0.6s ease ${index * 0.1}s`;
        observer.observe(el);
    });
    
    // Form validation + GA4 form_submit
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.style.borderColor = '#ef4444';
                } else {
                    field.style.borderColor = '#d1d5db';
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                return;
            }

            if (typeof gtag === 'function' && form.id === 'contactForm') {
                const servicioField = form.querySelector('[name="servicio"]');
                gtag('event', 'form_submit', {
                    event_category: 'contact',
                    event_label: 'contacto',
                    servicio: servicioField ? servicioField.value : 'no_especificado'
                });
            }
        });
    });
    
    // Parallax effect for hero section
    const hero = document.querySelector('.hero');
    if (hero) {
        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;
            const parallaxSpeed = 0.5;
            hero.style.transform = `translateY(${scrolled * parallaxSpeed}px)`;
        });
    }
    
    // Counter animation for stats
    const animateCounter = (element, target, duration = 2000) => {
        let current = 0;
        const increment = target / (duration / 16);
        const isPercentage = element.textContent.includes('%');
        const prefix = element.textContent.match(/[€$]/)?.[0] || '';
        const suffix = isPercentage ? '%' : '';
        
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }
            element.textContent = prefix + Math.floor(current) + suffix;
        }, 16);
    };
    
    // Observe stat elements for counter animation
    const statObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && !entry.target.classList.contains('animated')) {
                entry.target.classList.add('animated');
                const text = entry.target.textContent;
                const number = parseInt(text.replace(/[^\d]/g, ''));
                if (number) {
                    animateCounter(entry.target, number);
                }
            }
        });
    }, { threshold: 0.5 });
    
    document.querySelectorAll('.stat h3, .result-card h3, .metric-value').forEach(stat => {
        statObserver.observe(stat);
    });
    
    // WhatsApp float button animation + GA4 click_whatsapp
    const whatsappFloat = document.querySelector('.whatsapp-float');
    if (whatsappFloat) {
        whatsappFloat.addEventListener('click', function() {
            if (typeof gtag === 'function') {
                gtag('event', 'click_whatsapp', {
                    event_category: 'contact',
                    event_label: 'whatsapp_float'
                });
            }
        });
        setTimeout(() => {
            whatsappFloat.style.animation = 'pulse 2s infinite, fadeInUp 0.5s ease';
        }, 2000);
    }
    
    // Canvas Particles Animation for Hero
    const canvas = document.getElementById('hero-particles');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        let particles = [];
        let animationFrameId;

        const resizeCanvas = () => {
            canvas.width = canvas.offsetWidth;
            canvas.height = canvas.offsetHeight;
        };

        window.addEventListener('resize', resizeCanvas);
        resizeCanvas();

        class Particle {
            constructor() {
                this.x = Math.random() * canvas.width;
                this.y = Math.random() * canvas.height;
                this.size = Math.random() * 2 + 1;
                this.speedX = Math.random() * 1 - 0.5;
                this.speedY = Math.random() * -1 - 0.5;
                this.opacity = Math.random() * 0.5 + 0.1;
            }
            update() {
                this.x += this.speedX;
                this.y += this.speedY;
                if (this.y < 0) {
                    this.y = canvas.height;
                    this.x = Math.random() * canvas.width;
                }
                if (this.x < 0) this.x = canvas.width;
                if (this.x > canvas.width) this.x = 0;
            }
            draw() {
                ctx.fillStyle = `rgba(96, 165, 250, ${this.opacity})`;
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
                ctx.fill();
            }
        }

        const initParticles = () => {
            particles = [];
            const particleCount = Math.min(Math.floor(window.innerWidth / 10), 100);
            for (let i = 0; i < particleCount; i++) {
                particles.push(new Particle());
            }
        };

        const animateParticles = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // Draw connecting lines
            for (let i = 0; i < particles.length; i++) {
                for (let j = i; j < particles.length; j++) {
                    const dx = particles[i].x - particles[j].x;
                    const dy = particles[i].y - particles[j].y;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    
                    if (distance < 100) {
                        ctx.beginPath();
                        ctx.strokeStyle = `rgba(147, 197, 253, ${0.15 * (1 - distance/100)})`;
                        ctx.lineWidth = 0.5;
                        ctx.moveTo(particles[i].x, particles[i].y);
                        ctx.lineTo(particles[j].x, particles[j].y);
                        ctx.stroke();
                    }
                }
            }

            particles.forEach(p => {
                p.update();
                p.draw();
            });
            animationFrameId = requestAnimationFrame(animateParticles);
        };

        initParticles();
        animateParticles();
        
        // Pause animation if user prefers reduced motion
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            cancelAnimationFrame(animationFrameId);
            ctx.clearRect(0, 0, canvas.width, canvas.height);
        }
    }
    
    console.log('🚀 Megasoluciones web loaded successfully!');

    // GA4: eventos de conversión
    function trackEvent(name, params) {
        if (typeof gtag === 'function') {
            gtag('event', name, params || {});
        }
    }
    document.querySelectorAll('.btn-primary, .btn-secondary').forEach(function(btn) {
        btn.addEventListener('click', function() {
            trackEvent('click_cta', {
                link_text: (btn.textContent || '').trim().slice(0, 80),
                link_url: btn.getAttribute('href') || '',
                page_path: window.location.pathname
            });
        });
    });
    document.querySelectorAll('form.contact-form').forEach(function(form) {
        form.addEventListener('submit', function() {
            var action = form.getAttribute('action') || '';
            trackEvent('form_submit', { form_name: action, page_path: window.location.pathname });
            if (action.indexOf('checklist') !== -1) {
                trackEvent('generate_lead', { lead_type: 'checklist_automatizacion' });
            }
        });
    });
    if (window.location.pathname.indexOf('checklist') !== -1 && document.querySelector('.alert-success')) {
        trackEvent('generate_lead', { lead_type: 'checklist_automatizacion', step: 'success_page' });
    }
});
