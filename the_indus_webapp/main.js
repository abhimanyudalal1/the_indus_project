// Force browser to start at the top on every refresh
if ('scrollRestoration' in history) {
    history.scrollRestoration = 'manual';
}
window.scrollTo(0, 0);

const MAPTILER_KEY = 'WbFCpkLmnPET09LHSMz5';

const map = new maplibregl.Map({
    container: 'map',
    style: `https://api.maptiler.com/maps/satellite-v4/style.json?key=${MAPTILER_KEY}`,
    center: [77.0, 35.0],
    zoom: 6.5,
    pitch: 0,
    bearing: 0,
    interactive: false
});
// style: `https://api.maptiler.com/maps/hybrid-v4/style.json?key=${MAPTILER_KEY}`,

let cameraRolled = false;
let tarbelaMarkerEl = null;
let markerTimeout = null;
const scroller = scrollama();

map.on('load', () => {
    // Initialize Tarbela Marker Element
    const el = document.createElement('div');
    el.className = 'tarbela-marker-container';
    el.innerHTML = `
        <div class="tarbela-marker-pulse"></div>
        <div class="tarbela-marker-label">Tarbela Reservoir<br><span style="font-size:0.9rem; font-weight:300;">Streamflow Prediction Point</span> <br><span style="font-size:0.9rem; font-weight:300;">Transition: Natural → Regulated system</span></div>
    `;
    tarbelaMarkerEl = el;

    const popupHTML = `
        <div class="tarbela-popup-content">
            <h3>Why Tarbela Dam?</h3>
            <p><em>Three reasons, each stronger than the last.</em></p>
            <ol>
                <li><strong>Reliable long-term discharge records</strong><br>Ground-based streamflow measurement in the UIB is extremely sparse. Most gauging stations are inaccessible or have gaps. Tarbela has quality-controlled records going back decades because WAPDA operates it as critical national infrastructure.</li>
                <li><strong> Integrating point for the basin</strong><br>By the time water reaches Tarbela, it has collected runoff from the Karakoram, Hindu Kush, and Himalayan ranges. Every hydrological process happening upstream shows up in the Tarbela signal.</li>
                <li><strong>Highest real-world impact</strong><br>Tarbela is Pakistan's largest reservoir — supplying irrigation to ~12M acres of farmland and generating ~4,800 MW of hydropower. Reservoir operators need monthly forecasts to decide water release schedules. A skillful forecast here has direct operational value.</li>
            </ol>
        </div>
    `;

    const popup = new maplibregl.Popup({ offset: 25, closeButton: true, closeOnClick: true })
        .setHTML(popupHTML);

    new maplibregl.Marker({ element: el })
        .setLngLat([72.7383, 34.0897])
        .setPopup(popup)
        .addTo(map);

    // 1. ADD SOURCES
    map.addSource('snowzo', { type: 'geojson', data: '/animation/snowzo.geojson' });
    map.addSource('main_stem', { type: 'geojson', data: '/animation/main_stem.geojson' });
    map.addSource('major_tributaries', { type: 'geojson', data: '/animation/major_tributaries.geojson' });
    map.addSource('minor_trib', { type: 'geojson', data: '/animation/minor_trib.geojson' });
    map.addSource('upperindusbd', { type: 'geojson', data: '/animation/upperindusbd.geojson' });

    // 2. ADD LAYERS (Bottom to Top)

    // UIB Subbasins boundary pattern
    map.addLayer({
        id: 'uib-subbasins-layer',
        type: 'line',
        source: 'upperindusbd',
        paint: {
            'line-color': '#000200ea',
            'line-width': 4,
            'line-opacity': 1
        }
    });

    map.addLayer({
        id: 'snowzone-layer',
        type: 'fill',
        source: 'snowzo',
        paint: {
            'fill-color': '#ffffff',
            'fill-opacity': 0.7159
        }
    });

    map.addLayer({
        id: 'minor-network-layer',
        type: 'line',
        source: 'minor_trib',
        paint: {
            'line-color': '#38bdf8',
            'line-width': 1.1,
            'line-opacity': 0.7
        }
    });

    map.addLayer({
        id: 'major-tribs-layer',
        type: 'line',
        source: 'major_tributaries',
        paint: {
            'line-color': '#0284c7',
            'line-width': 3.5,
            'line-opacity': 0.8
        },
        filter: ['>=', ['get', 'DIST_DN_KM'], 2850]
    });

    map.addLayer({
        id: 'main-stem-layer',
        type: 'line',
        source: 'main_stem',
        paint: {
            'line-color': '#0ea5e9',
            'line-width': 6,
            'line-opacity': 0.9
        },
        filter: ['>=', ['get', 'DIST_DN_KM'], 2400]
    });

    setupScrollytelling();
});

function setupScrollytelling() {
    scroller
        .setup({
            step: '.step',
            progress: true,
            offset: 0.5,
            debug: false
        })
        .onStepProgress(handleStepProgress);
}

function handleStepProgress(response) {
    const scrollPercent = response.progress; // 0.0 to 1.0

    // 1. Snow opacity
    let snowOp = 0.7159;
    if (scrollPercent <= 0.5) {
        snowOp = 0.7159 - (scrollPercent / 0.5) * (0.7159 - 0.1686);
    } else {
        snowOp = 0.1686;
    }
    if (map.getLayer('snowzone-layer')) map.setPaintProperty('snowzone-layer', 'fill-opacity', snowOp);

    // 2. Minor tributaries remain static UI texture at 0.6 opacity
    if (map.getLayer('minor-network-layer')) map.setPaintProperty('minor-network-layer', 'line-opacity', 0.6);


    // 3. Major tributaries flow (Scroll 30% to 60%)
    let majorDist = 2850;
    if (scrollPercent > 0.3) {
        const majorProgress = Math.min(1.0, (scrollPercent - 0.3) / 0.3);
        majorDist = 2850 - majorProgress * (2850 - 2200);
    }
    if (map.getLayer('major-tribs-layer')) map.setFilter('major-tribs-layer', ['>=', ['get', 'DIST_DN_KM'], majorDist]);

    // 4. Main stem flow (Scroll 50% to 90%)
    let mainDist = 2400;
    if (scrollPercent > 0.5) {
        const mainProgress = Math.min(1.0, (scrollPercent - 0.5) / 0.4);
        mainDist = 2400 - mainProgress * (2400 - 1718);
    }
    if (map.getLayer('main-stem-layer')) map.setFilter('main-stem-layer', ['>=', ['get', 'DIST_DN_KM'], mainDist]);

    // 5. Timeline UI Updates
    const timelineProgress = document.getElementById('timeline-progress');
    const labels = document.querySelectorAll('.timeline-label');
    
    // Scale height maps directly to scroll percent until Camera Roll triggers at 0.95
    const uiPercent = Math.min(scrollPercent / 0.95, 1.0) * 100;
    timelineProgress.style.height = `${uiPercent}%`;

    // Timeline Colors based on progression
    // 0-30%: Snow Accumulation (White)
    // 30-60%: Active Melting Phase (Red)
    // 60%+: River Flow Routing (Blue)
    let color = '#ffffff'; 
    let activeIndex = 0;
    
    if (scrollPercent >= 0.95) {
        activeIndex = 3;
        color = '#0ea5e9';
    } else if (scrollPercent >= 0.60) {
        activeIndex = 2;
        color = '#0ea5e9'; // River Routing Blue
    } else if (scrollPercent >= 0.30) {
        activeIndex = 1;
        color = '#ef4444'; // Melt Red
    }
    
    timelineProgress.style.backgroundColor = color;

    // Highlight active label
    labels.forEach((label, i) => {
        if (i === activeIndex) {
            label.classList.add('active');
            label.querySelector('.dot').style.borderColor = color;
            label.querySelector('.dot').style.backgroundColor = color;
        } else {
            label.classList.remove('active');
            label.querySelector('.dot').style.borderColor = '#cbd5e1';
            label.querySelector('.dot').style.backgroundColor = '#1e293b';
        }
    });

    // 6. Camera Roll & Legend Visibility
    const legend = document.getElementById('map-legend');
    const timelineContainer = document.getElementById('timeline-container');
    const act2Overlay = document.getElementById('act2-overlay');

    if (scrollPercent >= 0.95) {
        if (!cameraRolled) {
            cameraRolled = true;
            timelineContainer.style.opacity = '0'; // Ease out timeline
            
            clearTimeout(markerTimeout);

            map.flyTo({ center: [72.8983, 33.9897], zoom: 11, pitch: 60, bearing: -20, duration: 4000 });
            
            // Show Tarbela marker and Act 2 overlay when camera stabilizes
            markerTimeout = setTimeout(() => {
                if (tarbelaMarkerEl) {
                     tarbelaMarkerEl.style.opacity = '1';
                     tarbelaMarkerEl.style.pointerEvents = 'auto';
                }
                if (act2Overlay) {
                     act2Overlay.style.opacity = '1';
                     act2Overlay.style.transform = 'translateY(0)';
                }
            }, 3500);
        }
    } else {
        if (cameraRolled) {
            cameraRolled = false;
            clearTimeout(markerTimeout);
            timelineContainer.style.opacity = '1'; // Ease in timeline
            if (tarbelaMarkerEl) {
                 tarbelaMarkerEl.style.opacity = '0';
                 tarbelaMarkerEl.style.pointerEvents = 'none';
            }
            if (act2Overlay) {
                 act2Overlay.style.opacity = '0';
                 act2Overlay.style.transform = 'translateY(100%)';
            }
            map.flyTo({ center: [77.0, 35.0], zoom: 6.5, pitch: 0, bearing: 0, duration: 3000 });
        }
    }

    if (legend) {
        legend.style.opacity = scrollPercent >= 0.95 ? '0' : '1';
    }
}

// Handle window resize
window.addEventListener('resize', () => {
    scroller.resize();
});

// Carousel Navigation Logic
const carousel = document.getElementById('act2-carousel');
const navBtns = document.querySelectorAll('.nav-btn');

if (carousel && navBtns.length > 0) {
    // Navigate on click
    navBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const idx = parseInt(btn.getAttribute('data-index'));
            const cardWidth = carousel.clientWidth;
            carousel.scrollTo({
                left: idx * cardWidth,
                behavior: 'smooth'
            });
        });
    });

    // Update active button on scroll
    carousel.addEventListener('scroll', () => {
        const cardWidth = carousel.clientWidth;
        const scrollPos = carousel.scrollLeft;
        const activeIdx = Math.round(scrollPos / cardWidth);

        navBtns.forEach((btn, i) => {
            if (i === activeIdx) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
    });

    // Map vertical mouse wheel to horizontal scroll inside the carousel natively
    carousel.addEventListener('wheel', (e) => {
        if (e.deltaY !== 0) {
            // Check if we are at horizontal limits
            const isAtStart = carousel.scrollLeft === 0;
            const isAtEnd = carousel.scrollLeft + carousel.clientWidth >= carousel.scrollWidth - 1;

            if (!isAtStart && e.deltaY < 0) {
                e.preventDefault();
                carousel.scrollLeft += e.deltaY;
            } else if (!isAtEnd && e.deltaY > 0) {
                e.preventDefault();
                carousel.scrollLeft += e.deltaY;
            }
        }
    });
}
