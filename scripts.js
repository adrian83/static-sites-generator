document.addEventListener('DOMContentLoaded', function () {
    const links = document.querySelectorAll('a');
    links.forEach((link) => {
        link.addEventListener('mouseenter', () => {
            link.style.opacity = '0.8';
        });
        link.addEventListener('mouseleave', () => {
            link.style.opacity = '';
        });
    });

    const navDropdowns = document.querySelectorAll('.nav-dropdown');
    navDropdowns.forEach((dropdown) => {
        const toggle = dropdown.querySelector('.nav-toggle');
        const list = dropdown.querySelector('.nav-list');

        if (!toggle || !list) {
            return;
        }

        toggle.addEventListener('click', (event) => {
            event.stopPropagation();
            list.classList.toggle('open');
            const expanded = list.classList.contains('open');
            toggle.setAttribute('aria-expanded', expanded);
        });
    });

    document.addEventListener('click', () => {
        navDropdowns.forEach((dropdown) => {
            const toggle = dropdown.querySelector('.nav-toggle');
            const list = dropdown.querySelector('.nav-list');
            if (toggle && list) {
                list.classList.remove('open');
                toggle.setAttribute('aria-expanded', 'false');
            }
        });
    });

    // Tag cloud toggle
    const tagCountsToggle = document.querySelector('.tag-counts-toggle');
    const tagCountsContent = document.querySelector('.tag-counts-content');
    if (tagCountsToggle && tagCountsContent) {
        tagCountsToggle.addEventListener('click', (event) => {
            event.stopPropagation();
            tagCountsContent.classList.toggle('open');
            const expanded = tagCountsContent.classList.contains('open');
            tagCountsToggle.setAttribute('aria-expanded', expanded);
        });
    }

    // Lightweight lightbox for event galleries
    const lightbox = document.getElementById('lightbox');
    if (lightbox) {
        const lbImage = lightbox.querySelector('.lb-image');
        const btnClose = lightbox.querySelector('.lb-close');
        const btnPrev = lightbox.querySelector('.lb-prev');
        const btnNext = lightbox.querySelector('.lb-next');

        let images = [];
        let current = 0;

        function openLightbox(index) {
            current = index;
            lbImage.src = images[current];
            lightbox.classList.add('open');
            lightbox.setAttribute('aria-hidden', 'false');
            document.body.style.overflow = 'hidden';
        }

        function closeLightbox() {
            lightbox.classList.remove('open');
            lightbox.setAttribute('aria-hidden', 'true');
            lbImage.src = '';
            document.body.style.overflow = '';
        }

        function showNext() {
            if (images.length === 0) return;
            current = (current + 1) % images.length;
            lbImage.src = images[current];
        }

        function showPrev() {
            if (images.length === 0) return;
            current = (current - 1 + images.length) % images.length;
            lbImage.src = images[current];
        }

        // Initialize galleries
        document.querySelectorAll('.event-gallery').forEach((gallery) => {
            const links = Array.from(gallery.querySelectorAll('a'));
            if (links.length === 0) return;
            images = links.map(l => l.getAttribute('href'));

            links.forEach((link, idx) => {
                link.addEventListener('click', (ev) => {
                    ev.preventDefault();
                    openLightbox(idx);
                });
            });

            // Detect image orientation and add portrait/landscape classes
            document.querySelectorAll('.event-gallery img').forEach((img) => {
                if (img.complete) {
                    setOrientationClass(img);
                } else {
                    img.addEventListener('load', () => setOrientationClass(img));
                }
            });

            function setOrientationClass(img) {
                const wrapper = img.closest('.event-gallery') || img.parentElement;
                if (!wrapper) return;
                if (img.naturalHeight > img.naturalWidth) {
                    img.classList.add('portrait');
                    img.classList.remove('landscape');
                } else {
                    img.classList.add('landscape');
                    img.classList.remove('portrait');
                }
            }
        });

        // Controls
        btnClose.addEventListener('click', closeLightbox);
        btnNext.addEventListener('click', showNext);
        btnPrev.addEventListener('click', showPrev);

        lightbox.addEventListener('click', (ev) => {
            if (ev.target === lightbox) closeLightbox();
        });

        document.addEventListener('keydown', (ev) => {
            if (!lightbox.classList.contains('open')) return;
            if (ev.key === 'Escape') closeLightbox();
            if (ev.key === 'ArrowRight') showNext();
            if (ev.key === 'ArrowLeft') showPrev();
        });
    }
});
