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
const scroller = scrollama();

map.on('load', () => {
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
            'line-width': 1,
            'line-opacity': 0.6
        }
    });

    map.addLayer({
        id: 'major-tribs-layer',
        type: 'line',
        source: 'major_tributaries',
        paint: {
            'line-color': '#0284c7',
            'line-width': 2.5,
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
            'line-width': 4,
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

    // 5. UI Updates
    const title = document.getElementById('narrative-title');
    const sub = document.getElementById('narrative-sub');
    const box = document.querySelector('.narrative-box');
    box.classList.add('is-active');

    if (scrollPercent < 0.3) {
        title.innerText = 'Upper Indus Basin';
        sub.innerText = 'Peak snowpack accumulation mapping at ~71% coverage in April.';
    } else if (scrollPercent < 0.6) {
        title.innerText = 'Summer Melt';
        sub.innerText = 'Temperatures rise, snowpack depletes rapidly, feeding the high-altitude Order 6/7 tributaries.';
    } else if (scrollPercent < 0.95) {
        title.innerText = 'Flow Routing';
        sub.innerText = 'The main stem gathers momentum, carrying billions of cubic meters downstream.';
    } else {
        title.innerText = 'Tarbela Dam';
        sub.innerText = 'The anchor point. The largest earth-filled dam in the world.';
    }

    // 6. Camera Roll
    if (scrollPercent >= 0.95 && !cameraRolled) {
        cameraRolled = true;
        map.flyTo({ center: [72.6990, 34.0875], zoom: 11, pitch: 60, bearing: -20, duration: 4000 });
    } else if (scrollPercent < 0.92 && cameraRolled) {
        cameraRolled = false;
        map.flyTo({ center: [77.0, 35.0], zoom: 6.5, pitch: 0, bearing: 0, duration: 3000 });
    }
}

// Handle window resize
window.addEventListener('resize', () => {
    scroller.resize();
});
