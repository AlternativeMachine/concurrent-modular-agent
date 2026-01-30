import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { CSS3DRenderer, CSS3DObject } from 'three/addons/renderers/CSS3DRenderer.js';

// Module data structure
let modules = [];

// Three.js setup
let scene, camera, webglRenderer, css3dRenderer, controls;
let moduleCards = [];
let memoryCard = null;
let titleCard = null;
let dynamicLinks = []; // Array to hold dynamic links with decay
let animationEnabled = true;
let raycaster, mouse;
let currentLayout = 'grid'; // 'grid' or 'circle'
let linkDecayTime = 5000; // Default 5 seconds in milliseconds

// Popup vector visualization
let popupScene, popupCamera, popupRenderer, popupControls;
let popupVectorData = [];
let popupVectorMeshes = [];
let popupConnectionLines = [];
let popupAnimationFrame = null;
let popupRaycaster, popupMouse;
let hoveredParticle = null;

const webglCanvas = document.getElementById('webgl-canvas');
const css3dCanvas = document.getElementById('css3d-canvas');
const container = document.getElementById('container');

// Status colors
const STATUS_COLORS = {
    active: 0x4ade80,
    processing: 0xfbbf24,
    idle: 0x6b7280,
    error: 0xef4444
};

// API configuration
const API_BASE_URL = 'http://localhost:8080';

// Fetch modules from API
async function fetchModules() {
    try {
        const response = await fetch(`${API_BASE_URL}/modules`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();

        // API returns: {"modules": ["conversation", "vision", ...]}
        if (!data.modules || !Array.isArray(data.modules)) {
            throw new Error('Invalid API response format');
        }

        // Convert module names to module objects
        modules = data.modules.map((name, index) => ({
            id: `M${index + 1}`,
            name: name,
            status: 'idle', // Default status
            enabled: true
        }));

        console.log('Modules loaded from API:', modules);
        return modules;
    } catch (error) {
        console.error('Error fetching modules:', error);
        // Show error message on screen
        showError(`Failed to load modules from API: ${error.message}`);
        throw error;
    }
}

// Display error message on screen
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: rgba(239, 68, 68, 0.95);
        color: white;
        padding: 30px 40px;
        border-radius: 12px;
        font-size: 18px;
        z-index: 10000;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
        max-width: 80%;
        text-align: center;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    `;
    errorDiv.textContent = message;
    document.body.appendChild(errorDiv);
}

// Initialize Three.js scene
function initThreeJS() {
    // Shared scene and camera
    scene = new THREE.Scene();

    camera = new THREE.PerspectiveCamera(
        50,
        window.innerWidth / window.innerHeight,
        1,
        5000
    );
    // Top-down view looking straight down
    camera.position.set(0, 0, 1000);
    camera.lookAt(0, 0, 0);

    // WebGL Renderer for vectors
    webglRenderer = new THREE.WebGLRenderer({
        canvas: webglCanvas,
        alpha: true,
        antialias: true
    });
    webglRenderer.setSize(window.innerWidth, window.innerHeight);
    webglRenderer.setPixelRatio(window.devicePixelRatio);
    webglRenderer.setClearColor(0x0a0a0a, 1);

    // CSS3D Renderer for HTML cards
    css3dRenderer = new CSS3DRenderer({ element: css3dCanvas });
    css3dRenderer.setSize(window.innerWidth, window.innerHeight);

    // Controls - restrict to keep top-down view
    controls = new OrbitControls(camera, webglCanvas); // Use webglCanvas instead of css3dCanvas
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.enableRotate = false; // Disable rotation to maintain top-down view
    controls.minDistance = 500;
    controls.maxDistance = 2000;

    // Raycaster
    raycaster = new THREE.Raycaster();
    mouse = new THREE.Vector2();

    // Lighting for WebGL scene
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.6);
    directionalLight.position.set(50, 100, 50);
    scene.add(directionalLight);

    const pointLight1 = new THREE.PointLight(0x4a9eff, 1.5, 500);
    pointLight1.position.set(-150, 100, 200);
    scene.add(pointLight1);

    const pointLight2 = new THREE.PointLight(0x4ade80, 1.5, 500);
    pointLight2.position.set(150, 100, 200);
    scene.add(pointLight2);

    // Event listeners
    window.addEventListener('resize', onWindowResize);
    css3dCanvas.addEventListener('click', onCanvasClick);
    css3dCanvas.addEventListener('mousemove', onMouseMove);

    // Create UI elements
    createTitle();
    createModuleCards();
    createMemoryCard();
    createLegend();
}

function createTitle() {
    const titleDiv = document.createElement('div');
    titleDiv.className = 'title';
    titleDiv.textContent = 'CMA - Concurrent Modular Agent Monitor';

    const titleObject = new CSS3DObject(titleDiv);

    // Calculate position based on visible area
    const vFOV = THREE.MathUtils.degToRad(camera.fov);
    const visibleHeight = 2 * Math.tan(vFOV / 2) * Math.abs(camera.position.z);
    const visibleTop = visibleHeight / 2;

    // Title height in 3D space (approx 70px * 0.6 scale = 42)
    const titleHeight = 42;
    const topMargin = 20;

    const yPosition = visibleTop - titleHeight / 2 - topMargin;

    titleObject.position.set(0, yPosition, 0);
    titleObject.scale.set(0.6, 0.6, 0.6);
    scene.add(titleObject);

    titleCard = titleObject;
}

function updateTitlePosition() {
    if (!titleCard) return;

    // Recalculate position on resize
    const vFOV = THREE.MathUtils.degToRad(camera.fov);
    const visibleHeight = 2 * Math.tan(vFOV / 2) * Math.abs(camera.position.z);
    const visibleTop = visibleHeight / 2;

    const titleHeight = 42;
    const topMargin = 20;

    const yPosition = visibleTop - titleHeight / 2 - topMargin;
    titleCard.position.y = yPosition;
}

function createModuleCards() {
    modules.forEach((module, idx) => {
        const pos = getCardPosition(idx, 'grid');

        // Create HTML card
        const cardDiv = document.createElement('div');
        cardDiv.className = `module-card ${module.status}`;
        cardDiv.innerHTML = `
            <div class="status-indicator ${module.status}"></div>
            <div class="module-name" data-full-name="${module.name}">${module.name}</div>
            <div class="module-toggle">
                <div class="toggle-switch ${module.enabled ? 'on' : ''}" data-module-id="${module.id}">
                    <div class="toggle-slider"></div>
                </div>
                <span class="toggle-label">${module.enabled ? 'ON' : 'OFF'}</span>
            </div>
        `;

        // Create CSS3DObject
        const cardObject = new CSS3DObject(cardDiv);
        cardObject.position.set(pos.x, pos.y, 0);
        cardObject.scale.set(0.6, 0.6, 0.6);
        cardObject.userData = { module, type: 'moduleCard', element: cardDiv, index: idx };

        scene.add(cardObject);
        moduleCards.push(cardObject);

        // Add toggle handler first
        const toggleSwitch = cardDiv.querySelector('.toggle-switch');
        const toggleLabel = cardDiv.querySelector('.toggle-label');

        toggleSwitch.addEventListener('click', (e) => {
            e.stopPropagation();
            e.preventDefault();
            console.log('Toggle clicked for module:', module.id);
            toggleModule(module.id);
        });

        toggleSwitch.addEventListener('touchstart', (e) => {
            e.stopPropagation();
            e.preventDefault();
            toggleModule(module.id);
        });

        // Add click handler for card (not toggle)
        cardDiv.addEventListener('click', (e) => {
            // Don't highlight if clicking on toggle area
            if (e.target.closest('.module-toggle')) {
                return;
            }
            e.stopPropagation();
            highlightModuleVectors(module.id);
        });

        // Add tooltip functionality for module name
        const moduleNameElement = cardDiv.querySelector('.module-name');
        const tooltip = document.getElementById('moduleNameTooltip');

        moduleNameElement.addEventListener('mouseenter', (e) => {
            const fullName = e.target.getAttribute('data-full-name');
            // Only show tooltip if text is truncated
            if (e.target.scrollWidth > e.target.clientWidth) {
                tooltip.textContent = fullName;
                tooltip.classList.add('show');
                updateTooltipPosition(e);
            }
        });

        moduleNameElement.addEventListener('mousemove', (e) => {
            if (tooltip.classList.contains('show')) {
                updateTooltipPosition(e);
            }
        });

        moduleNameElement.addEventListener('mouseleave', () => {
            tooltip.classList.remove('show');
        });
    });

    // Create connection lines between module cards (example)
    createModuleConnections();
}

function updateTooltipPosition(event) {
    const tooltip = document.getElementById('moduleNameTooltip');
    tooltip.style.left = (event.clientX + 15) + 'px';
    tooltip.style.top = (event.clientY + 15) + 'px';
}

function getCardPosition(index, layout) {
    if (layout === 'grid') {
        const cardsPerRow = 4;
        const cardSpacing = 300;
        const rowSpacing = 220;
        const startX = -(cardsPerRow - 1) * cardSpacing / 2;
        const startY = 280;

        const row = Math.floor(index / cardsPerRow);
        const col = index % cardsPerRow;
        const x = startX + col * cardSpacing;
        const y = startY - row * rowSpacing;

        return { x, y };
    } else if (layout === 'circle') {
        // Calculate available space for circle
        const vFOV = THREE.MathUtils.degToRad(camera.fov);
        const visibleHeight = 2 * Math.tan(vFOV / 2) * Math.abs(camera.position.z);
        const visibleTop = visibleHeight / 2;
        const visibleBottom = -visibleHeight / 2;

        // Title dimensions and position
        const titleHeight = 42;
        const titleMargin = 20;
        const titleBottom = visibleTop - titleHeight - titleMargin;

        // Margins for circle
        const topCircleMargin = 60; // Space below title
        const bottomCircleMargin = 60; // Space from bottom

        // Available boundaries
        const topBoundary = titleBottom - topCircleMargin;
        const bottomBoundary = visibleBottom + bottomCircleMargin;
        const availableSpace = topBoundary - bottomBoundary;

        // Center Y position and radius
        const circleY = bottomBoundary + availableSpace / 2;
        const radius = Math.min(350, availableSpace / 2.2); // Fit radius with padding

        const angleStep = (Math.PI * 2) / modules.length;
        const angle = index * angleStep - Math.PI / 2; // Start from top

        const x = Math.cos(angle) * radius;
        const y = Math.sin(angle) * radius + circleY;

        return { x, y };
    }
}

function switchLayout(newLayout) {
    if (currentLayout === newLayout) return;

    currentLayout = newLayout;

    // Clear all existing links
    for (let i = dynamicLinks.length - 1; i >= 0; i--) {
        const link = dynamicLinks[i];
        scene.remove(link.line);
        link.line.geometry.dispose();
        link.material.dispose();
    }
    dynamicLinks = [];

    // Animate cards to new positions
    moduleCards.forEach((cardObject, idx) => {
        const targetPos = getCardPosition(idx, newLayout);
        animateCardPosition(cardObject, targetPos);
    });

    // Animate memory card position based on layout
    animateMemoryCardPosition(newLayout);

    // Update toggle state
    const toggle = document.getElementById('layout-toggle');
    const modeText = document.getElementById('layout-mode-text');

    if (newLayout === 'circle') {
        toggle.classList.add('circle');
        modeText.textContent = 'Circle';
    } else {
        toggle.classList.remove('circle');
        modeText.textContent = 'Grid';
    }
}

function animateCardPosition(cardObject, targetPos) {
    const startPos = {
        x: cardObject.position.x,
        y: cardObject.position.y
    };

    const duration = 1000; // 1 second
    const startTime = Date.now();

    function animate() {
        const now = Date.now();
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Easing function (ease-in-out)
        const eased = progress < 0.5
            ? 2 * progress * progress
            : -1 + (4 - 2 * progress) * progress;

        cardObject.position.x = startPos.x + (targetPos.x - startPos.x) * eased;
        cardObject.position.y = startPos.y + (targetPos.y - startPos.y) * eased;

        if (progress < 1) {
            requestAnimationFrame(animate);
        }
    }

    animate();
}

function createModuleConnections() {
    // Start spawning random dynamic links
    setInterval(() => {
        spawnRandomLink();
    }, 300); // Spawn a new link every 300ms (was 800ms)
}

function spawnRandomLink() {
    if (moduleCards.length < 1 || !memoryCard) return;

    // Get enabled modules only
    const enabledIndices = modules
        .map((m, idx) => ({ module: m, idx }))
        .filter(({ module }) => module.enabled)
        .map(({ idx }) => idx);

    if (enabledIndices.length < 1) return;

    // Randomly decide: module-to-module, module-to-memory, or memory-to-module
    const rand = Math.random();
    let from, to, linkType;

    if (rand < 0.33) {
        // Link from module to memory (33%)
        linkType = 'to-memory';
        const fromIdx = enabledIndices[Math.floor(Math.random() * enabledIndices.length)];
        from = moduleCards[fromIdx].position;
        to = memoryCard.position;
    } else if (rand < 0.66) {
        // Link from memory to module (33%)
        linkType = 'from-memory';
        from = memoryCard.position;
        const toIdx = enabledIndices[Math.floor(Math.random() * enabledIndices.length)];
        to = moduleCards[toIdx].position;
    } else {
        // Link between two modules (34%)
        linkType = 'module-to-module';
        if (enabledIndices.length < 2) return;

        const fromIdx = enabledIndices[Math.floor(Math.random() * enabledIndices.length)];
        let toIdx = enabledIndices[Math.floor(Math.random() * enabledIndices.length)];

        // Ensure different modules
        while (toIdx === fromIdx && enabledIndices.length > 1) {
            toIdx = enabledIndices[Math.floor(Math.random() * enabledIndices.length)];
        }

        from = moduleCards[fromIdx].position;
        to = moduleCards[toIdx].position;
    }

    // Create curved line using quadratic bezier curve
    const curve = new THREE.QuadraticBezierCurve3(
        new THREE.Vector3(from.x, from.y, from.z),
        new THREE.Vector3(
            (from.x + to.x) / 2 + (Math.random() - 0.5) * 50,
            (from.y + to.y) / 2,
            (from.z + to.z) / 2
        ),
        new THREE.Vector3(to.x, to.y, to.z)
    );

    const points = curve.getPoints(100);
    const geometry = new THREE.BufferGeometry().setFromPoints(points);

    // Add distance along the line as a vertex attribute
    const distances = new Float32Array(points.length);
    let totalDistance = 0;
    distances[0] = 0;
    for (let i = 1; i < points.length; i++) {
        totalDistance += points[i].distanceTo(points[i - 1]);
        distances[i] = totalDistance;
    }
    // Normalize distances to 0-1 range
    for (let i = 0; i < distances.length; i++) {
        distances[i] /= totalDistance;
    }
    geometry.setAttribute('lineDistance', new THREE.BufferAttribute(distances, 1));

    // Color based on link type - brighter and more vibrant colors
    let color;
    if (linkType === 'module-to-module') {
        color = new THREE.Color(0x5fff9f); // Brighter green - module to module
    } else if (linkType === 'to-memory') {
        color = new THREE.Color(0xff5555); // Brighter red - to memory
    } else if (linkType === 'from-memory') {
        color = new THREE.Color(0x5fadff); // Brighter blue - from memory
    }

    // Create gradient stripe shader material
    const material = new THREE.ShaderMaterial({
        uniforms: {
            color: { value: color },
            time: { value: 0 },
            opacity: { value: 1.0 }
        },
        vertexShader: `
            attribute float lineDistance;
            varying float vLineDistance;

            void main() {
                vLineDistance = lineDistance;
                gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }
        `,
        fragmentShader: `
            uniform vec3 color;
            uniform float time;
            uniform float opacity;
            varying float vLineDistance;

            void main() {
                // Create moving stripes along the line
                float stripe = sin((vLineDistance * 15.0 - time * 3.5) * 3.14159);
                float intensity = smoothstep(0.1, 0.9, stripe);

                // Mix between dark and bright - stronger contrast
                vec3 finalColor = color * (0.7 + intensity * 0.8);

                gl_FragColor = vec4(finalColor, opacity);
            }
        `,
        transparent: true,
        depthWrite: false,
        linewidth: 2
    });

    const line = new THREE.Line(geometry, material);
    scene.add(line);

    // Add to dynamic links array with creation time and lifetime
    // If linkDecayTime is Infinity (max slider value), set lifetime to Infinity
    const lifetime = linkDecayTime === Infinity ? Infinity : linkDecayTime;

    dynamicLinks.push({
        line: line,
        material: material,
        curve: curve,
        createdAt: Date.now(),
        lifetime: lifetime,
        initialOpacity: 1.0,
        initialColor: color.clone()
    });
}

function updateDynamicLinks() {
    const now = Date.now();

    // Update and remove expired links
    for (let i = dynamicLinks.length - 1; i >= 0; i--) {
        const link = dynamicLinks[i];
        const age = now - link.createdAt;

        // Update shader time for animated stripes
        link.material.uniforms.time.value = age * 0.001; // Convert to seconds

        // If lifetime is Infinity, keep the link at full opacity
        if (link.lifetime === Infinity) {
            link.material.uniforms.opacity.value = link.initialOpacity;
            link.material.uniforms.color.value.copy(link.initialColor);
        } else if (age >= link.lifetime) {
            // Remove expired link
            scene.remove(link.line);
            link.line.geometry.dispose();
            link.material.dispose();
            dynamicLinks.splice(i, 1);
        } else {
            // Fade out based on age
            const fadeProgress = age / link.lifetime;
            const opacity = link.initialOpacity * (1 - fadeProgress);
            link.material.uniforms.opacity.value = opacity;

            // Optional: slight color shift as it fades
            const colorShift = 1 - fadeProgress * 0.3;
            const fadedColor = link.initialColor.clone().multiplyScalar(colorShift);
            link.material.uniforms.color.value.copy(fadedColor);
        }
    }
}

function createMemoryCard() {
    const memoryDiv = document.createElement('div');
    memoryDiv.className = 'memory-card';
    memoryDiv.innerHTML = `
        <div class="memory-title">Memory</div>
        <div class="memory-subtitle">Long-term Storage & Knowledge Base</div>
    `;

    // Use click event with immediate execution
    memoryDiv.addEventListener('click', (e) => {
        console.log('Memory card clicked!');
        e.stopPropagation();
        e.preventDefault();

        try {
            console.log('Calling openMemoryPopup...');
            openMemoryPopup();
            console.log('openMemoryPopup called successfully');
        } catch (error) {
            console.error('Error opening popup:', error);
        }
    });

    // Prevent context menu
    memoryDiv.addEventListener('contextmenu', (e) => {
        e.preventDefault();
    });

    const memoryObject = new CSS3DObject(memoryDiv);

    // Calculate position based on visible area
    const vFOV = THREE.MathUtils.degToRad(camera.fov);
    const visibleHeight = 2 * Math.tan(vFOV / 2) * Math.abs(camera.position.z);
    const visibleBottom = -visibleHeight / 2;

    // Memory card height in 3D space (200px * 0.5 scale = 100)
    const memoryCardHeight = 100;
    const bottomMargin = 30; // Small margin from bottom

    const yPosition = visibleBottom + memoryCardHeight / 2 + bottomMargin;

    memoryObject.position.set(0, yPosition, 0);
    memoryObject.scale.set(0.5, 0.5, 0.5);
    scene.add(memoryObject);

    memoryCard = memoryObject;

    console.log('Memory card created with click handler');
}

function updateMemoryCardPosition() {
    if (!memoryCard) return;

    if (currentLayout === 'circle') {
        // Calculate circle center Y - same as getCardPosition
        const vFOV = THREE.MathUtils.degToRad(camera.fov);
        const visibleHeight = 2 * Math.tan(vFOV / 2) * Math.abs(camera.position.z);
        const visibleTop = visibleHeight / 2;
        const visibleBottom = -visibleHeight / 2;

        const titleHeight = 42;
        const titleMargin = 20;
        const titleBottom = visibleTop - titleHeight - titleMargin;

        const topCircleMargin = 60;
        const bottomCircleMargin = 60;

        const topBoundary = titleBottom - topCircleMargin;
        const bottomBoundary = visibleBottom + bottomCircleMargin;
        const availableSpace = topBoundary - bottomBoundary;

        memoryCard.position.y = bottomBoundary + availableSpace / 2;
    } else {
        // In grid layout, place at bottom of screen
        const vFOV = THREE.MathUtils.degToRad(camera.fov);
        const visibleHeight = 2 * Math.tan(vFOV / 2) * Math.abs(camera.position.z);
        const visibleBottom = -visibleHeight / 2;

        const memoryCardHeight = 100;
        const bottomMargin = 30;

        const yPosition = visibleBottom + memoryCardHeight / 2 + bottomMargin;
        memoryCard.position.y = yPosition;
    }
}

function animateMemoryCardPosition(layout) {
    if (!memoryCard) return;

    const startY = memoryCard.position.y;
    let targetY;

    if (layout === 'circle') {
        // Calculate circle center Y - same as getCardPosition
        const vFOV = THREE.MathUtils.degToRad(camera.fov);
        const visibleHeight = 2 * Math.tan(vFOV / 2) * Math.abs(camera.position.z);
        const visibleTop = visibleHeight / 2;
        const visibleBottom = -visibleHeight / 2;

        const titleHeight = 42;
        const titleMargin = 20;
        const titleBottom = visibleTop - titleHeight - titleMargin;

        const topCircleMargin = 60;
        const bottomCircleMargin = 60;

        const topBoundary = titleBottom - topCircleMargin;
        const bottomBoundary = visibleBottom + bottomCircleMargin;
        const availableSpace = topBoundary - bottomBoundary;

        targetY = bottomBoundary + availableSpace / 2; // Center of circle
    } else {
        // Calculate bottom position for grid layout
        const vFOV = THREE.MathUtils.degToRad(camera.fov);
        const visibleHeight = 2 * Math.tan(vFOV / 2) * Math.abs(camera.position.z);
        const visibleBottom = -visibleHeight / 2;
        const memoryCardHeight = 100;
        const bottomMargin = 30;
        targetY = visibleBottom + memoryCardHeight / 2 + bottomMargin;
    }

    const duration = 1000; // 1 second - same as module cards
    const startTime = Date.now();

    function animate() {
        const now = Date.now();
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Easing function (ease-in-out) - same as module cards
        const eased = progress < 0.5
            ? 2 * progress * progress
            : -1 + (4 - 2 * progress) * progress;

        memoryCard.position.y = startY + (targetY - startY) * eased;

        if (progress < 1) {
            requestAnimationFrame(animate);
        }
    }

    animate();
}

function createLegend() {
    // Legend removed - vector store visualization removed
}

function updateModuleCard(cardObject) {
    const module = cardObject.userData.module;
    const element = cardObject.userData.element;

    // Update classes
    let className = `module-card ${module.status}`;
    if (!module.enabled) {
        className += ' disabled';
    }
    element.className = className;
    element.querySelector('.status-indicator').className = `status-indicator ${module.status}`;
}

function toggleModule(moduleId) {
    const module = modules.find(m => m.id === moduleId);
    if (!module) return;

    // Toggle enabled state
    module.enabled = !module.enabled;

    // Find the card and update UI
    const cardObject = moduleCards.find(c => c.userData.module.id === moduleId);
    if (cardObject) {
        const element = cardObject.userData.element;
        const toggleSwitch = element.querySelector('.toggle-switch');
        const toggleLabel = element.querySelector('.toggle-label');

        // Update toggle UI
        if (module.enabled) {
            toggleSwitch.classList.add('on');
            toggleLabel.textContent = 'ON';
        } else {
            toggleSwitch.classList.remove('on');
            toggleLabel.textContent = 'OFF';
        }

        // Update card appearance
        updateModuleCard(cardObject);

        // Hide/show vectors for this module
        updateVectorVisibility();
    }
}

function updateVectorVisibility() {
    // Vector visualization removed
}

function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();

    webglRenderer.setSize(window.innerWidth, window.innerHeight);
    css3dRenderer.setSize(window.innerWidth, window.innerHeight);

    // Update title and memory card positions on resize
    updateTitlePosition();
    updateMemoryCardPosition();
}

// Vector visualization removed

// Animation loop
function animate() {
    requestAnimationFrame(animate);

    // Update dynamic links (decay animation)
    updateDynamicLinks();

    controls.update();

    // Render both scenes
    webglRenderer.render(scene, camera);
    css3dRenderer.render(scene, camera);
}

function highlightModuleVectors(moduleId) {
    // Highlight module card
    moduleCards.forEach(cardObject => {
        const isHighlighted = cardObject.userData.module.id === moduleId;
        const scale = isHighlighted ? 0.66 : 0.6;
        cardObject.scale.set(scale, scale, scale);
    });
}

function onMouseMove(event) {
    mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
    mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
}

function onCanvasClick(event) {
    // Click handling removed - vector visualization removed
}

// Control functions
window.resetView = function() {
    camera.position.set(0, 0, 1000);
    camera.lookAt(0, 0, 0);
    controls.target.set(0, 0, 0);
    controls.update();
};

window.toggleAnimation = function() {
    animationEnabled = !animationEnabled;
};

// Simulate module status changes
function simulateModuleActivity() {
    setInterval(() => {
        const randomIdx = Math.floor(Math.random() * modules.length);
        const statuses = ['active', 'processing', 'idle'];
        modules[randomIdx].status = statuses[Math.floor(Math.random() * statuses.length)];

        if (moduleCards[randomIdx]) {
            updateModuleCard(moduleCards[randomIdx]);
        }
    }, 3000);
}

// Keyboard controls
window.addEventListener('keydown', (e) => {
    if (e.key === 'r' || e.key === 'R') {
        window.resetView();
    } else if (e.key === ' ') {
        e.preventDefault();
        window.toggleAnimation();
    }
});

// Memory popup functions
function openMemoryPopup() {
    const popup = document.getElementById('memoryPopup');
    popup.classList.add('show');

    initPopupVisualization();
    animatePopup();
}

function closeMemoryPopup() {
    const popup = document.getElementById('memoryPopup');
    const tooltip = document.getElementById('particleTooltip');

    // Hide tooltip
    tooltip.classList.remove('show');

    // Add closing animation
    popup.style.animation = 'fadeOut 0.3s ease forwards';

    setTimeout(() => {
        popup.classList.remove('show');
        popup.style.animation = '';

        // Stop animation
        if (popupAnimationFrame) {
            cancelAnimationFrame(popupAnimationFrame);
            popupAnimationFrame = null;
        }

        // Remove event listener
        const canvas = document.getElementById('popup-canvas');
        if (canvas) {
            canvas.removeEventListener('mousemove', onPopupMouseMove);
        }

        // Clean up
        if (popupRenderer) {
            popupVectorMeshes.forEach(mesh => {
                if (mesh.geometry) mesh.geometry.dispose();
                if (mesh.material) mesh.material.dispose();
            });
            popupConnectionLines.forEach(line => {
                if (line.geometry) line.geometry.dispose();
                if (line.material) line.material.dispose();
            });
            popupVectorMeshes = [];
            popupConnectionLines = [];
            popupVectorData = [];
        }

        // Reset hover state
        hoveredParticle = null;
    }, 300);
}

function initPopupVisualization() {
    const canvas = document.getElementById('popup-canvas');
    const parent = canvas.parentElement;

    // Scene
    popupScene = new THREE.Scene();
    popupScene.background = new THREE.Color(0x0a0a0a);

    // Camera
    popupCamera = new THREE.PerspectiveCamera(
        75,
        parent.clientWidth / parent.clientHeight,
        0.1,
        1000
    );
    popupCamera.position.z = 300;

    // Renderer
    popupRenderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    popupRenderer.setSize(parent.clientWidth, parent.clientHeight);
    popupRenderer.setPixelRatio(window.devicePixelRatio);

    // Controls
    popupControls = new OrbitControls(popupCamera, canvas);
    popupControls.enableDamping = true;
    popupControls.dampingFactor = 0.05;

    // Raycaster for hover detection
    popupRaycaster = new THREE.Raycaster();
    popupMouse = new THREE.Vector2();

    // Mouse move event for hover detection
    canvas.addEventListener('mousemove', onPopupMouseMove);

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
    popupScene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.6);
    directionalLight.position.set(50, 100, 50);
    popupScene.add(directionalLight);

    const pointLight1 = new THREE.PointLight(0x4a9eff, 1.5, 500);
    pointLight1.position.set(-150, 100, 200);
    popupScene.add(pointLight1);

    const pointLight2 = new THREE.PointLight(0x4ade80, 1.5, 500);
    pointLight2.position.set(150, 100, 200);
    popupScene.add(pointLight2);

    // Generate vectors
    generatePopupVectors();
}

function generatePopupVectors() {
    popupVectorData = [];
    popupVectorMeshes = [];
    popupConnectionLines = [];

    const bounds = 200;

    // Dummy text samples
    const dummyTexts = [
        "The quick brown fox jumps over the lazy dog. This is a sample text for testing.",
        "Machine learning models process vast amounts of data to identify patterns.",
        "Natural language processing enables computers to understand human language.",
        "Vector embeddings represent semantic meaning in high-dimensional space.",
        "Neural networks consist of interconnected layers of artificial neurons.",
        "Deep learning has revolutionized computer vision and speech recognition.",
        "Attention mechanisms allow models to focus on relevant input features.",
        "Transformer architecture has become the foundation of modern NLP.",
        "Gradient descent optimizes model parameters through iterative updates.",
        "Tokenization breaks text into smaller units for processing.",
        "Semantic search retrieves information based on meaning rather than keywords.",
        "Contextual embeddings capture word meaning based on surrounding text.",
        "Pre-trained models transfer knowledge from large-scale datasets.",
        "Fine-tuning adapts general models to specific tasks and domains.",
        "Retrieval augmented generation combines search with text generation."
    ];

    modules.forEach((module, idx) => {
        if (!module.enabled) return;

        const clusterCount = Math.floor(Math.random() * 15) + 10;
        const centerX = (Math.random() - 0.5) * bounds * 1.2;
        const centerY = (Math.random() - 0.5) * bounds * 1.2;
        const centerZ = (Math.random() - 0.5) * bounds * 0.5;

        for (let i = 0; i < clusterCount; i++) {
            const angle = Math.random() * Math.PI * 2;
            const phi = Math.random() * Math.PI;
            const radius = Math.random() * 40 + 10;

            const vec = {
                position: new THREE.Vector3(
                    centerX + Math.sin(phi) * Math.cos(angle) * radius,
                    centerY + Math.sin(phi) * Math.sin(angle) * radius,
                    centerZ + Math.cos(phi) * radius * 0.3
                ),
                module: module.id,
                moduleName: module.name,
                type: Math.random() > 0.5 ? 'query' : 'document',
                size: Math.random() * 2.5 + 2,
                highlighted: false,
                text: dummyTexts[Math.floor(Math.random() * dummyTexts.length)],
                timestamp: new Date(Date.now() - Math.random() * 86400000 * 7).toISOString().split('T')[0]
            };

            popupVectorData.push(vec);

            const geometry = new THREE.SphereGeometry(vec.size, 16, 16);
            const color = getPopupVectorColor(vec);
            const material = new THREE.MeshPhongMaterial({
                color: color,
                emissive: color,
                emissiveIntensity: 0.5,
                shininess: 100
            });
            const mesh = new THREE.Mesh(geometry, material);
            mesh.position.copy(vec.position);
            mesh.userData = vec;

            popupScene.add(mesh);
            popupVectorMeshes.push(mesh);
        }
    });

    createPopupConnections();
}

function getPopupVectorColor(vec) {
    if (vec.highlighted) {
        return 0xfbbf24;
    } else if (vec.type === 'query') {
        return 0x4a9eff;
    } else if (vec.type === 'document') {
        return 0x4ade80;
    } else {
        return 0xa78bfa;
    }
}

function createPopupConnections() {
    const lineMaterial = new THREE.LineBasicMaterial({
        color: 0x4a9eff,
        transparent: true,
        opacity: 0.15
    });

    for (let i = 0; i < popupVectorData.length; i++) {
        for (let j = i + 1; j < popupVectorData.length; j++) {
            const dist = popupVectorData[i].position.distanceTo(popupVectorData[j].position);

            if (dist < 30 && popupVectorData[i].module === popupVectorData[j].module) {
                const points = [popupVectorData[i].position, popupVectorData[j].position];
                const geometry = new THREE.BufferGeometry().setFromPoints(points);
                const line = new THREE.Line(geometry, lineMaterial);
                popupScene.add(line);
                popupConnectionLines.push(line);
            }
        }
    }
}

function onPopupMouseMove(event) {
    const canvas = document.getElementById('popup-canvas');
    const rect = canvas.getBoundingClientRect();

    // Calculate mouse position relative to canvas
    popupMouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    popupMouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    // Update raycaster
    popupRaycaster.setFromCamera(popupMouse, popupCamera);

    // Check for intersections
    const intersects = popupRaycaster.intersectObjects(popupVectorMeshes);

    const tooltip = document.getElementById('particleTooltip');
    const tooltipHeader = document.getElementById('tooltipHeader');
    const tooltipContent = document.getElementById('tooltipContent');
    const tooltipMeta = document.getElementById('tooltipMeta');

    if (intersects.length > 0) {
        const intersectedMesh = intersects[0].object;
        const particleData = intersectedMesh.userData;

        // Reset previous hover
        if (hoveredParticle && hoveredParticle !== intersectedMesh) {
            hoveredParticle.material.emissiveIntensity = 0.5;
        }

        // Highlight current particle
        hoveredParticle = intersectedMesh;
        intersectedMesh.material.emissiveIntensity = 1.0;

        // Show tooltip
        tooltipHeader.textContent = `${particleData.moduleName} - ${particleData.type}`;
        tooltipContent.textContent = particleData.text;
        tooltipMeta.textContent = `Module: ${particleData.module} | Date: ${particleData.timestamp}`;

        // Position tooltip near mouse
        tooltip.style.left = (event.clientX + 15) + 'px';
        tooltip.style.top = (event.clientY + 15) + 'px';
        tooltip.classList.add('show');
    } else {
        // Reset hover
        if (hoveredParticle) {
            hoveredParticle.material.emissiveIntensity = 0.5;
            hoveredParticle = null;
        }

        // Hide tooltip
        tooltip.classList.remove('show');
    }
}

function animatePopup() {
    if (!document.getElementById('memoryPopup').classList.contains('show')) {
        return;
    }

    popupAnimationFrame = requestAnimationFrame(animatePopup);

    // Update controls and render (no position updates - static visualization)
    popupControls.update();
    popupRenderer.render(popupScene, popupCamera);
}

// Initialize application
async function initApp() {
    try {
        // Fetch modules from API first
        await fetchModules();

        // Then initialize the UI
        initThreeJS();
        animate();
        simulateModuleActivity();
    } catch (error) {
        // Error already displayed by showError in fetchModules
        console.error('Application initialization failed:', error);
    }
}

// Start the application
initApp();

// Setup layout toggle
document.getElementById('layout-toggle').addEventListener('click', () => {
    const newLayout = currentLayout === 'grid' ? 'circle' : 'grid';
    switchLayout(newLayout);
});

// Setup popup close button
document.getElementById('closePopup').addEventListener('click', closeMemoryPopup);

// Setup decay slider
const decaySlider = document.getElementById('decay-slider');
const decayValue = document.getElementById('decay-value');

decaySlider.addEventListener('input', (e) => {
    const value = parseInt(e.target.value);
    const now = Date.now();

    if (value === 21) {
        // Max value - no decay (infinite)
        linkDecayTime = Infinity;
        decayValue.textContent = '∞';

        // Update all existing links to have infinite lifetime
        dynamicLinks.forEach(link => {
            link.lifetime = Infinity;
        });
    } else {
        // Convert seconds to milliseconds
        linkDecayTime = value * 1000;
        decayValue.textContent = value + 's';

        // Update ALL existing links to use new decay time
        dynamicLinks.forEach(link => {
            // Reset creation time to now so they all start fading from now
            link.createdAt = now;
            link.lifetime = linkDecayTime;
        });
    }
});
