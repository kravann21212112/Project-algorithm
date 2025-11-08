/* portfolio/js/projects.js
   Cleaned-up: removed HTML <script> tags (should be in HTML).
   Added safety checks so script doesn't throw if elements or libs are missing.
*/

document.addEventListener('DOMContentLoaded', () => {
  // Preloader
  const preloader = document.querySelector('.preloader');
  window.addEventListener('load', () => {
    if (preloader) {
      preloader.classList.add('hide');
      setTimeout(() => preloader.remove(), 600);
    }
  });

  // AOS (only if loaded)
  if (window.AOS && typeof AOS.init === 'function') {
    AOS.init({duration: 1000, once: true});
  }

  // Typewriter
  const txtRotateEls = document.querySelectorAll('.txt-rotate');
  if (txtRotateEls.length) {
    txtRotateEls.forEach(el => {
      try {
        const toRotate = JSON.parse(el.getAttribute('data-rotate'));
        const period = parseInt(el.getAttribute('data-period'), 10) || 2000;
        let loop = 0, txt = '', deleting = false;
        const tick = () => {
          const i = loop % toRotate.length;
          const full = toRotate[i];
          txt = deleting ? full.substring(0, txt.length - 1) : full.substring(0, txt.length + 1);
          el.innerHTML = `<span class="wrap">${txt}</span>`;
          let delta = 200 - Math.random() * 100;
          if (deleting) delta /= 2;
          if (!deleting && txt === full) { delta = period; deleting = true; }
          else if (deleting && txt === '') { deleting = false; loop++; delta = 500; }
          setTimeout(tick, delta);
        };
        tick();
      } catch (e) {
        // malformed data-rotate, skip
        // console.warn('txt-rotate parse error', e);
      }
    });
  }

  // Skill Progress
  const progressBars = document.querySelectorAll('.skill-progress');
  const skillSection = document.getElementById('skills');
  if (skillSection && progressBars.length && window.IntersectionObserver) {
    const observer = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting) {
        progressBars.forEach(bar => bar.style.width = bar.getAttribute('data-progress') + '%');
        observer.unobserve(skillSection);
      }
    }, {threshold: 0.5});
    observer.observe(skillSection);
  }

  // Portfolio Filter & Projects Loading (requires jQuery + isotope)
  if (window.jQuery && jQuery.fn && jQuery.fn.isotope) {
    const $ = window.jQuery;
    const $grid = $('.portfolio-grid').isotope({itemSelector: '.portfolio-item', layoutMode: 'fitRows'});
    
    // Load projects from backend
    fetch('http://localhost:5000/api/projects')
      .then(response => response.json())
      .then(projects => {
        const $portfolioGrid = $('.portfolio-grid');
        projects.forEach(project => {
          const projectHtml = `
            <div class="portfolio-item ${project.category || 'web'}" data-aos="fade-up">
              <div class="portfolio-card">
                <div class="portfolio-image">
                  <img src="${project.image || '../4bbc5c7f9365f56b36f3806bb40a1b9a.jpg'}" alt="${project.name}" style="width: 250px; height:200px;">
                  <div class="portfolio-overlay">
                    <div class="overlay-content">
                      <span class="project-category">${getCategoryName(project.category)}</span>
                      <h3 class="project-title">${project.name}</h3>
                      <p class="project-description">${project.description}</p>
                      <div class="project-links">
                        <a href="#" class="project-link"><i class="fas fa-external-link-alt"></i></a>
                        <a href="#" class="project-link"><i class="fab fa-github"></i></a>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="portfolio-info">
                  <div class="tech-stack">
                    <span class="tech-tag">React.js</span>
                    <span class="tech-tag">Node.js</span>
                    <span class="tech-tag">MongoDB</span>
                  </div>
                </div>
              </div>
            </div>`;
          $portfolioGrid.append(projectHtml);
        });
        
        // Re-initialize Isotope after adding items
        $grid.isotope('reloadItems').isotope();
      })
      .catch(error => console.error('Error loading projects:', error));

    // Category filter clicks
    $('.category-btn').on('click', function () {
      $('.category-btn').removeClass('active');
      $(this).addClass('active');
      $grid.isotope({filter: $(this).attr('data-filter')});
    });
  }

  // Helper function to convert category codes to display names
  function getCategoryName(category) {
    const categories = {
      'web': 'Web Development',
      'app': 'Mobile Apps',
      'ui': 'UI/UX Design'
    };
    return categories[category] || 'Web Development';
  }

  // Theme Toggle
  const themeToggle = document.getElementById('theme-toggle');
  const body = document.body;
  if (themeToggle) {
    if (localStorage.getItem('darkMode') === 'true') {
      body.classList.add('dark-theme');
      try { themeToggle.checked = true; } catch (e) {}
    }
    themeToggle.addEventListener('change', () => {
      body.classList.toggle('dark-theme');
      localStorage.setItem('darkMode', body.classList.contains('dark-theme'));
    });
  }

  // Mobile Menu
  const navToggle = document.querySelector('.nav-toggle');
  const navMenu = document.querySelector('.nav-menu');
  if (navToggle && navMenu) {
    navToggle.addEventListener('click', () => {
      navToggle.classList.toggle('active');
      navMenu.classList.toggle('show');
    });
  }

  // Smooth Scroll
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      const targetSelector = a.getAttribute('href');
      if (!targetSelector || targetSelector === '#' || targetSelector.length < 2) return;
      const target = document.querySelector(targetSelector);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({behavior: 'smooth'});
      }
    });
  });

  // Scroll Top
  const scrollTop = document.querySelector('.scroll-top');
  if (scrollTop) {
    window.addEventListener('scroll', () => scrollTop.classList.toggle('show', window.scrollY > 500));
    scrollTop.addEventListener('click', () => window.scrollTo({top: 0, behavior: 'smooth'}));
  }

  // Mouse Cursor
  const outer = document.querySelector('.cursor-outer');
  const inner = document.querySelector('.cursor-inner');
  if (outer && inner) {
    document.addEventListener('mousemove', e => {
      outer.style.transform = `translate(${e.clientX}px, ${e.clientY}px)`;
      inner.style.transform = `translate(${e.clientX}px, ${e.clientY}px)`;
    });
    document.querySelectorAll('a, button').forEach(el => {
      el.addEventListener('mouseenter', () => { outer.style.transform += ' scale(1.5)'; });
      el.addEventListener('mouseleave', () => { outer.style.transform = outer.style.transform.replace(' scale(1.5)', ''); });
    });
  }

  // Contact Form (Fake Success)
  const contactForm = document.getElementById('contact-form');
  if (contactForm) {
    contactForm.addEventListener('submit', e => {
      e.preventDefault();
      alert('Thank you! Your message has been sent.');
      e.target.reset();
    });
  }
});