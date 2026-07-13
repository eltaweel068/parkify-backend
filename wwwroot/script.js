// ============================================================
// Parkify Frontend — API Integration Layer
// Backend: Flask + Firebase | Auth: JWT (Bearer Token)
// ============================================================

const API_BASE   = 'https://meko.tryasp.net';
const PARKING_ID = 'parking_1';
const DEVICE_KEY = 'esp32_parking1_key';

// ── Cache Layer ───────────────────────────────────────────────
const CACHE = {
    dashboard:     'pkfy_dashboard',
    slots:         'pkfy_slots',
    bookings:      'pkfy_bookings',
    users:         'pkfy_users',
    alerts:        'pkfy_alerts',
    notifications: 'pkfy_notifications',
};
function cacheSet(key, data) {
    try { localStorage.setItem(key, JSON.stringify(data)); } catch(e) {}
}
function cacheGet(key) {
    try { return JSON.parse(localStorage.getItem(key) || 'null'); } catch(e) { return null; }
}

// ── Helpers ──────────────────────────────────────────────────
function getToken() {
    return localStorage.getItem('parkify_token');
}
function saveAuth(data) {
    localStorage.setItem('parkify_token', data.access_token);
    if (data.user) {
        localStorage.setItem('parkify_user', JSON.stringify(data.user));
    }
}
function clearAuth() {
    localStorage.removeItem('parkify_token');
    localStorage.removeItem('parkify_user');
}
function getUser() {
    try { return JSON.parse(localStorage.getItem('parkify_user')) || {}; }
    catch { return {}; }
}

async function apiFetch(endpoint, options = {}) {
    const token = getToken();
    const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    let res;
    try {
        res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
    } catch(networkErr) {
        throw new Error('Cannot connect to server — is the backend running?');
    }

    if (res.status === 401 || res.status === 403) {
        clearAuth();
        window.location.href = 'login.html';
        return null;
    }
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        let message = `Error ${res.status}`;
        if (typeof err.detail === 'string') message = err.detail;
        else if (Array.isArray(err.detail)) message = err.detail.map(e => e.msg).join(', ');
        else if (typeof err.message === 'string') message = err.message;
        throw new Error(message);
    }
    return res.json();
}

function showError(msg) {
    const el = document.getElementById('errorMsg') || document.getElementById('loginError');
    if (el) { el.textContent = msg; el.style.display = 'block'; }
    else alert(msg);
}
function showSuccess(msg) {
    const el = document.getElementById('successMsg');
    if (el) { el.textContent = msg; el.style.display = 'block'; }
}

// ── Password Toggle ───────────────────────────────────────────
function initPasswordToggle() {
    const toggle = document.querySelector('#togglePassword');
    const input  = document.querySelector('#password');
    if (toggle && input) {
        toggle.addEventListener('click', function () {
            const isPass = input.getAttribute('type') === 'password';
            input.setAttribute('type', isPass ? 'text' : 'password');
            this.classList.toggle('fa-eye');
            this.classList.toggle('fa-eye-slash');
        });
    }
}

// ════════════════════════════════════════════════════════════
// 1. REGISTER
// ════════════════════════════════════════════════════════════
function initRegister() {
    const form = document.getElementById('registerForm');
    if (!form) return;

    form.addEventListener('submit', async function (e) {
        e.preventDefault();
        const btn = form.querySelector('button[type="submit"]');
        btn.disabled = true;
        btn.textContent = 'Registering...';

        // Hide previous errors
        const errEl = document.getElementById('errorMsg');
        if (errEl) errEl.style.display = 'none';

        const first_name = document.getElementById('first_name')?.value.trim();
        const last_name  = document.getElementById('last_name')?.value.trim();
        const email      = document.getElementById('email')?.value.trim();
        const password   = document.getElementById('password')?.value;
        const phone      = document.getElementById('phone')?.value.trim();

        // Build body — only include phone if filled
        const body = { name: `${first_name} ${last_name}`.trim(), email, password };
        if (phone) body.phone = phone;

        try {
            await apiFetch('/api/v1/auth/register', {
                method: 'POST',
                body: JSON.stringify(body)
            });
            // Show success then redirect
            const succEl = document.getElementById('successMsg');
            if (succEl) { succEl.textContent = 'Account created! Redirecting to login...'; succEl.style.display = 'block'; }
            setTimeout(() => window.location.href = 'login.html', 1500);
        } catch (err) {
            showError(err.message);
            btn.disabled = false;
            btn.textContent = 'Register';
        }
    });
}

// ════════════════════════════════════════════════════════════
// 2. LOGIN
// ════════════════════════════════════════════════════════════
function initLogin() {
    const form = document.getElementById('loginForm');
    if (!form) return;

    form.addEventListener('submit', async function (e) {
        e.preventDefault();
        const btn = form.querySelector('button[type="submit"]');
        btn.disabled = true;
        btn.textContent = 'Signing in...';

        const email    = document.getElementById('email')?.value.trim();
        const password = document.getElementById('password')?.value;

        try {
            const data = await apiFetch('/api/v1/auth/login', {
                method: 'POST',
                body: JSON.stringify({ email, password })
            });
            saveAuth(data);
            window.location.href = 'dashboard.html';
        } catch (err) {
            showError(err.message || 'Invalid email or password');
            btn.disabled = false;
            btn.textContent = 'Sign In';
        }
    });
}

// ════════════════════════════════════════════════════════════
// 3. DASHBOARD — Guard & Profile
// ════════════════════════════════════════════════════════════
function guardDashboard() {
    if (!getToken()) {
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

// ── Dashboard Charts ──────────────────────────────────────────
let occupancyChartObj = null;
let revenueChartObj   = null;

function initDashboardCharts() {
    const occCanvas = document.getElementById('occupancyChart');
    const revCanvas = document.getElementById('revenueChart');
    if (!occCanvas || !revCanvas) return;
    if (typeof Chart === 'undefined') { setTimeout(initDashboardCharts, 500); return; }

    if (occupancyChartObj) { occupancyChartObj.destroy(); occupancyChartObj = null; }
    if (revenueChartObj)   { revenueChartObj.destroy();   revenueChartObj   = null; }

    // Occupancy: 24 hour labels
    const hourLabels = Array.from({length: 25}, (_, i) => String(i).padStart(2,'0') + ':00');
    const occData    = Array(25).fill(null);
    const nowHr      = new Date().getHours();
    for (let i = 0; i <= nowHr; i++) occData[i] = 0;

    occupancyChartObj = new Chart(occCanvas, {
        type: 'line',
        data: {
            labels: hourLabels,
            datasets: [{ label: 'Occupancy %', data: occData, borderColor: '#6b21a8',
                backgroundColor: 'rgba(107,33,168,0.08)', borderWidth: 2, fill: true,
                tension: 0.4, pointRadius: 2, spanGaps: false }]
        },
        options: { responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { min: 0, max: 100, ticks: { callback: v => v + '%', stepSize: 25 }, grid: { color: '#f1f5f9' } },
                x: { grid: { color: '#f1f5f9' }, ticks: { maxTicksLimit: 8, maxRotation: 0 } }
            }
        }
    });

    // Revenue: Mon-Sun bars
    revenueChartObj = new Chart(revCanvas, {
        type: 'bar',
        data: {
            labels: ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'],
            datasets: [{ label: 'Revenue (EGP)', data: [0,0,0,0,0,0,0],
                backgroundColor: '#059669', borderRadius: 6, borderSkipped: false, barPercentage: 0.6 }]
        },
        options: { responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false },
                tooltip: { callbacks: { label: ctx => ` ${ctx.parsed.y.toFixed(0)} EGP` } } },
            scales: {
                y: { beginAtZero: true, grid: { color: '#f1f5f9' }, ticks: { callback: v => v + ' EGP' } },
                x: { grid: { display: false } }
            }
        }
    });
}

function updateChartsFromBookings(bookings) {
    if (!revenueChartObj) return;
    const revenue = [0,0,0,0,0,0,0];
    const now = new Date();
    const startOfWeek = new Date(now);
    startOfWeek.setDate(now.getDate() - ((now.getDay() + 6) % 7));
    startOfWeek.setHours(0,0,0,0);
    bookings.forEach(b => {
        if (!b.created_at) return;
        const d = new Date(b.created_at);
        if (d < startOfWeek) return;
        const idx = (d.getDay() + 6) % 7;
        revenue[idx] += Number(b.amount || b.total_amount || 0);
    });
    revenueChartObj.data.datasets[0].data = revenue;
    revenueChartObj.update('none');
}

function updateOccupancyChart(pct) {
    if (!occupancyChartObj) return;
    const h = new Date().getHours();
    occupancyChartObj.data.datasets[0].data[h] = pct;
    occupancyChartObj.update('none');
}

function initProfileDisplay() {
    const user = getUser();
    const name  = user.first_name && user.last_name
        ? `${user.first_name} ${user.last_name}`
        : user.first_name || user.username || user.name || 'Admin';
    const email = user.email || 'admin@grandmall.com';

    const nameTop      = document.getElementById('displayUserNameTop');
    const nameDrop     = document.getElementById('displayUserNameDropdown');
    const emailDrop    = document.getElementById('displayUserEmailDropdown');

    if (nameTop)   nameTop.textContent  = name;
    if (nameDrop)  nameDrop.textContent = name;
    if (emailDrop) emailDrop.textContent = email;

    const signOutBtn = document.getElementById('signOutBtn');
    if (signOutBtn) {
        signOutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            clearAuth();
            window.location.href = 'login.html';
        });
    }
}

// ════════════════════════════════════════════════════════════
// 4. DASHBOARD STATS — /api/v1/admin/dashboard
// ════════════════════════════════════════════════════════════
function renderDashboardStats(data) {
    const stats    = data.data || data;
    const visitors = stats.active_visitors ?? stats.current_visitors ?? 0;
    const el = (id) => document.getElementById(id);
    if (el('statVisitors')) el('statVisitors').innerHTML = `${visitors} <span class="stat-sub">Currently</span>`;
    loadFloorList(stats);
    if (stats.recent_bookings) loadRecentBookings(stats.recent_bookings);
}

function updateRevenueFromBookings(bookings) {
    // Calculate today's revenue from actual bookings
    const today = new Date().toDateString();
    const todayRevenue = bookings
        .filter(b => b.created_at && new Date(b.created_at).toDateString() === today)
        .reduce((sum, b) => sum + Number(b.amount || b.total_amount || 0), 0);
    const el = document.getElementById('statRevenue');
    if (el) el.innerHTML = `${todayRevenue.toFixed(0)} EGP <span class="stat-sub">Today</span>`;
}

async function loadDashboardStats() {
    // Show cached data instantly
    const cached = cacheGet(CACHE.dashboard);
    if (cached) renderDashboardStats(cached);

    try {
        const data = await apiFetch('/api/v1/admin/dashboard');
        if (!data) return;
        cacheSet(CACHE.dashboard, data);
        renderDashboardStats(data);

    } catch (err) {
        console.error('Dashboard stats error:', err);
    }
}

function loadFloorList(stats) {
    const floorList = document.getElementById('floorList');
    if (!floorList) return;

    const floors = stats.floors || [{
        name: 'Ground Floor',
        available: stats.available_spots ?? 8,
        total: stats.total_spots ?? 8
    }];

    floorList.innerHTML = floors.map(floor => {
        const pct = floor.total ? Math.round(((floor.total - floor.available) / floor.total) * 100) : 0;
        return `
        <div class="floor-item">
            <div class="floor-info">
                <span class="floor-name">${floor.name || 'Ground Floor'}</span>
                <span class="floor-stats">${floor.available ?? 0} / ${floor.total ?? 0} available</span>
            </div>
            <div class="floor-bar-wrap">
                <div class="floor-bar">
                    <div class="floor-bar-fill" style="width:${pct}%"></div>
                </div>
                <span class="floor-pct">${pct}%</span>
            </div>
        </div>`;
    }).join('');
}

function loadRecentBookings(bookings) {
    const bookingList = document.getElementById('bookingList');
    if (!bookingList) return;

    if (!bookings.length) {
        bookingList.innerHTML = '<p class="empty-msg">No recent bookings</p>';
        return;
    }

    bookingList.innerHTML = bookings.slice(0, 5).map(b => {
        const statusClass = b.status === 'active' ? 'active' : b.status === 'completed' ? 'available' : 'pending';
        return `
        <div class="booking-item">
            <div class="booking-spot">${b.spot_id || b.slot_id || '--'}</div>
            <div class="booking-user">${b.user_name || b.user?.username || 'Unknown'}</div>
            <span class="badge-status ${statusClass}">${b.status || '--'}</span>
        </div>`;
    }).join('');
}

// ════════════════════════════════════════════════════════════
// 5. PARKING SPOTS — /api/v1/admin/parkings + /slots
// ════════════════════════════════════════════════════════════
let currentParkingId = localStorage.getItem('parkify_parking_id') || 'parking_1';

// Slot IDs matching the parking map zones
const HTML_SLOT_IDS = new Set([
    'parking_1_slot_A1', 'parking_1_slot_A2',
    'parking_1_slot_B1', 'parking_1_slot_B2',
    'parking_1_slot_C1', 'parking_1_slot_C2',
    'parking_1_slot_D1', 'parking_1_slot_D2',
]);

function filterMySlots(slots) {
    return slots.filter(s => {
        const slotNum = s.slot_number || '';
        const id = s.slot_id || s.id || (slotNum ? `parking_1_slot_${slotNum}` : '');
        return HTML_SLOT_IDS.has(id);
    });
}

async function loadParkingSpots() {
    // Show cached slots instantly
    const cachedSlots = cacheGet(CACHE.slots);
    if (cachedSlots) {
        const mySlots = filterMySlots(cachedSlots);
        updateSpotsGrid(mySlots);
        updateSpotStats(mySlots);
        initSpotModal();
    }

    try {
        const parkingsData = await apiFetch('/api/v1/admin/parkings');
        if (!parkingsData) return;

        const parkings = parkingsData.data || parkingsData.parkings || parkingsData;
        if (!parkings.length) return;

        const parking = parkings[0];
        currentParkingId = parking.id || parking.parking_id || 'parking_1';
        localStorage.setItem('parkify_parking_id', currentParkingId);

        const slotsData = await apiFetch(`/api/v1/admin/parkings/${currentParkingId}/slots`);
        if (!slotsData) return;

        const allSlots = slotsData.data || slotsData.slots || slotsData;
        const slots    = filterMySlots(allSlots);
        cacheSet(CACHE.slots, slots);

        // Initialize previous statuses for change detection
        slots.forEach(s => {
            const slotNum = s.slot_number || '';
            const id = s.slot_id || s.id || (slotNum ? `parking_1_slot_${slotNum}` : '');
            if (id) prevSlotStatuses[id] = (s.status || '').toLowerCase();
        });

        updateSpotsGrid(slots);
        updateSpotStats(slots);
        initSpotModal();

        // Update dashboard main cards with correct 8-slot numbers
        const counts = { available: 0, occupied: 0, reserved: 0, maintenance: 0 };
        slots.forEach(s => {
            const st = (s.status || 'available').toLowerCase();
            if (counts[st] !== undefined) counts[st]++;
        });
        const total = slots.length;
        const occ   = total ? Math.round(((counts.occupied + counts.reserved) / total) * 100) : 0;
        const el    = id => document.getElementById(id);
        if (el('statAvailable')) el('statAvailable').innerHTML = `${counts.available} <span class="stat-sub">/ ${total}</span>`;
        if (el('statOccupancy')) el('statOccupancy').innerHTML = `${occ}% <span class="stat-sub">Overall</span>`;
        const pFill = document.querySelector('.progress-fill');
        const pText = document.querySelector('.progress-text');
        if (pFill) pFill.style.width = `${occ}%`;
        if (pText) pText.textContent  = `${occ}%`;

        // Update occupancy chart
        updateOccupancyChart(occ);

    } catch (err) {
        console.error('Parking spots error:', err);
    }
}

function updateSpotsGrid(slots) {
    const spotBoxes = document.querySelectorAll('.spot-box');

    // Build slot map — handle both slot_id and slot_number
    const slotMap = {};
    slots.forEach(s => {
        const slotNum = s.slot_number || '';
        // Try slot_id first, then build from slot_number
        const id = s.slot_id || s.id ||
            (slotNum ? `parking_1_slot_${slotNum}` : null);
        if (id) slotMap[id] = s;
        // Also index by slot_number directly
        if (slotNum) slotMap[slotNum] = s;
    });

    spotBoxes.forEach(box => {
        const boxId = box.dataset.id; // e.g. parking_1_slot_A02
        const slot  = slotMap[boxId];
        if (!slot) return;

        const status = (slot.status || 'available').toLowerCase();
        // Display: extract after _slot_ or use as-is
        const displayName = slot.slot_number ||
            (boxId.includes('_slot_') ? boxId.split('_slot_')[1] : boxId);

        const statusMap = { available: 'free', occupied: 'taken', reserved: 'reserved', maintenance: 'maintenance' };
        const cssClass  = statusMap[status] || 'free';
        const label     = status.charAt(0).toUpperCase() + status.slice(1);

        box.className         = `spot-box ${cssClass}`;
        box.dataset.status    = label;
        box.dataset.parkingId = currentParkingId || PARKING_ID;

        const idEl     = box.querySelector('.spot-id');
        const footerEl = box.querySelector('.spot-footer');
        if (idEl)     idEl.textContent = displayName;
        if (footerEl) footerEl.textContent = label;
    });
}

function updateSpotStats(slots) {
    const counts = { available: 0, occupied: 0, reserved: 0, maintenance: 0 };
    slots.forEach(s => {
        const status = (s.status || 'available').toLowerCase();
        if (counts[status] !== undefined) counts[status]++;
    });
    const total = slots.length;
    const occ   = total ? Math.round(((counts.occupied + counts.reserved) / total) * 100) : 0;

    // Save to localStorage so it persists
    localStorage.setItem('parkify_spot_stats', JSON.stringify({ ...counts, total, occ }));

    // Spots page stats grid
    const statNums = document.querySelectorAll('.spot-stat-card .stat-num');
    if (statNums[0]) statNums[0].textContent = total;
    if (statNums[1]) statNums[1].textContent = counts.available;
    if (statNums[2]) statNums[2].textContent = counts.occupied;
    if (statNums[3]) statNums[3].textContent = counts.reserved;
    if (statNums[4]) statNums[4].textContent = counts.maintenance;

    // Dashboard main stat cards
    const statAvailable = document.getElementById('statAvailable');
    if (statAvailable) statAvailable.innerHTML = `${counts.available} <span class="stat-sub">/ ${total}</span>`;
    const statOccupancy = document.getElementById('statOccupancy');
    if (statOccupancy) statOccupancy.innerHTML = `${occ}% <span class="stat-sub">Overall</span>`;
    const trendAvailable = document.getElementById('trendAvailable');
    if (trendAvailable) trendAvailable.textContent = `${total ? Math.round((counts.available / total) * 100) : 0}%`;
    const trendOccupancy = document.getElementById('trendOccupancy');
    if (trendOccupancy) trendOccupancy.textContent = `${occ}%`;

    // Sidebar progress
    const progressFill = document.querySelector('.progress-fill');
    const progressText = document.querySelector('.progress-text');
    if (progressFill) progressFill.style.width = `${occ}%`;
    if (progressText) progressText.textContent  = `${occ}%`;

    // Floor overview
    const floorMetrics = document.querySelectorAll('.metric .m-value');
    if (floorMetrics[0]) floorMetrics[0].textContent = total;
    if (floorMetrics[1]) { floorMetrics[1].textContent = counts.available; floorMetrics[1].className = 'm-value text-green'; }
    if (floorMetrics[2]) { floorMetrics[2].textContent = counts.occupied;  floorMetrics[2].className = 'm-value text-red'; }

    const fpPct  = document.querySelector('.fp-percentage');
    const fpFill = document.querySelector('.fp-fill');
    if (fpPct)  fpPct.textContent  = `${occ}%`;
    if (fpFill) fpFill.style.width = `${occ}%`;

    const fStatValues = document.querySelectorAll('.f-stat-value');
    if (fStatValues[1]) fStatValues[1].textContent = total;
    if (fStatValues[2]) fStatValues[2].textContent = counts.available;
    if (fStatValues[3]) fStatValues[3].textContent = `${occ}%`;
}

// ════════════════════════════════════════════════════════════
// 6. USERS — /api/v1/admin/users
// ════════════════════════════════════════════════════════════
async function loadUsers() {
    const cached = cacheGet(CACHE.users);
    if (cached) renderUsersGrid(cached);

    try {
        const data = await apiFetch('/api/v1/admin/users');
        if (!data) return;
        const users = data.data || data.users || data;
        cacheSet(CACHE.users, users);
        renderUsersGrid(users);
    } catch (err) {
        console.error('Users error:', err);
    }
}

function renderUsersGrid(users) {
    const container = document.getElementById('visitorsGridContainer');
    if (!container) return;

    if (!users.length) {
        container.innerHTML = '<p class="empty-msg">No users found</p>';
        return;
    }

    container.innerHTML = users.map(user => {
        const name     = user.username || user.name || 'Unknown';
        const email    = user.email || '—';
        const phone    = user.phone || '—';
        const joinDate = user.created_at ? new Date(user.created_at).toLocaleDateString() : '—';
        const status   = user.is_suspended ? 'Suspended' : (user.is_active !== false ? 'Active' : 'Inactive');
        const statusCls= status === 'Active' ? 'active' : 'inactive';
        const initials = name.slice(0, 2).toUpperCase();
        const colors   = ['#7c3aed','#0891b2','#059669','#d97706','#dc2626'];
        const color    = colors[name.charCodeAt(0) % colors.length];
        const bookings = user.total_bookings ?? 0;

        return `
        <div class="visitor-card">
            <div class="v-card-header">
                <div class="v-avatar" style="background-color:${color}">${initials}</div>
                <div class="v-info">
                    <h4>${name}</h4>
                    <span class="v-status ${statusCls}">${status}</span>
                </div>
                <button class="v-menu-btn"><i class="fa-solid fa-ellipsis-vertical"></i></button>
            </div>
            <div class="v-card-body">
                <p><i class="fa-regular fa-envelope"></i> ${email}</p>
                <p><i class="fa-solid fa-phone"></i> ${phone}</p>
                <p><i class="fa-regular fa-calendar"></i> ${joinDate}</p>
            </div>
            <div class="v-card-footer">
                <div class="v-stat"><span>Total Bookings</span><strong>${bookings}</strong></div>
                <div class="v-stat"><span>Active Now</span><strong class="text-blue">${status === 'Active' ? 1 : 0}</strong></div>
            </div>
        </div>`;
    }).join('');

    // Search functionality
    const searchInput = document.querySelector('.visitors-search-bar input');
    if (searchInput) {
        searchInput.addEventListener('input', function () {
            const q = this.value.toLowerCase();
            container.querySelectorAll('.visitor-card').forEach(card => {
                const text = card.textContent.toLowerCase();
                card.style.display = text.includes(q) ? '' : 'none';
            });
        });
    }
}

// ════════════════════════════════════════════════════════════
// 7. BOOKINGS / PAYMENTS — /api/v1/admin/bookings
// ════════════════════════════════════════════════════════════
async function loadBookings() {
    const cached = cacheGet(CACHE.bookings);
    if (cached) { renderPaymentsTable(cached); updatePaymentStats(cached); updateChartsFromBookings(cached); updateRevenueFromBookings(cached); }

    try {
        const data = await apiFetch('/api/v1/admin/bookings');
        if (!data) return;
        const bookings = data.data || data.bookings || data;
        cacheSet(CACHE.bookings, bookings);
        renderPaymentsTable(bookings);
        updatePaymentStats(bookings);
        updateChartsFromBookings(bookings);
        updateRevenueFromBookings(bookings);
    } catch (err) {
        console.error('Bookings error:', err);
    }
}

function renderPaymentsTable(bookings) {
    const tbody = document.getElementById('paymentsTableBody');
    if (!tbody) return;

    if (!bookings.length) {
        tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;padding:20px">No payments found</td></tr>';
        return;
    }

    tbody.innerHTML = bookings.map((b, i) => {
        const date      = b.created_at ? new Date(b.created_at).toLocaleDateString('en-US', { year:'numeric', month:'short', day:'numeric', hour:'2-digit', minute:'2-digit' }) : '—';
        const amount    = Number(b.amount || b.total_amount || 0).toFixed(2);
        const duration  = b.duration_hours ? `${Math.floor(b.duration_hours)}h ${Math.round((b.duration_hours % 1) * 60)}m` : '—';
        const status    = (b.status || 'pending').toLowerCase();
        const statusCls = status === 'completed' ? 'available' : status === 'active' || status === 'confirmed' || status === 'checked_in' ? 'active' : 'pending';
        const user      = b.user_name || b.user?.username || 'Unknown';
        const userEmail = b.user_email || b.user?.email || '';
        const spot      = b.slot_number || b.slot_id || b.spot_id || '—';
        const method    = b.payment_method || 'Cash';
        const bookingId = b.id || b.booking_id;

        // Action buttons based on status
        const isActive  = ['active', 'confirmed', 'reserved'].includes(status);
        const isCheckedIn = status === 'checked_in' || status === 'active';
        let actions = '—';
        if (isCheckedIn) {
            actions = `<button onclick="adminCheckout('${bookingId}')" 
                style="background:#059669;color:#fff;border:none;padding:4px 10px;border-radius:6px;cursor:pointer;font-size:12px;font-weight:600;">
                <i class="fa-solid fa-car-side"></i> Check-out</button>`;
        } else if (isActive) {
            actions = `
                <div style="display:flex;gap:6px;flex-wrap:wrap;">
                    <button onclick="adminCheckin('${bookingId}')"
                        style="background:#6b21a8;color:#fff;border:none;padding:4px 10px;border-radius:6px;cursor:pointer;font-size:12px;font-weight:600;">
                        <i class="fa-solid fa-right-to-bracket"></i> Check-in</button>
                    <button onclick="adminCancelBooking('${bookingId}', '${spot}')"
                        style="background:#dc2626;color:#fff;border:none;padding:4px 10px;border-radius:6px;cursor:pointer;font-size:12px;font-weight:600;">
                        <i class="fa-solid fa-xmark"></i> Cancel</button>
                </div>`;
        }

        return `
        <tr id="booking-row-${bookingId}">
            <td class="td-id">${bookingId || `PAY-${String(i + 1).padStart(3, '0')}`}</td>
            <td><div class="td-user"><strong>${user}</strong><span>${userEmail}</span></div></td>
            <td><div class="td-loc"><strong>Grand Mall</strong><span>${spot}</span></div></td>
            <td class="td-amount"><strong>${amount} EGP</strong></td>
            <td class="td-duration">${duration}</td>
            <td class="td-method">${method}</td>
            <td><span class="badge-status ${statusCls}" id="booking-status-${bookingId}">${status}</span></td>
            <td class="td-date">${date}</td>
            <td id="booking-actions-${bookingId}">${actions}</td>
        </tr>`;
    }).join('');
}

async function adminCheckin(bookingId) {
    try {
        await apiFetch(`/api/v1/bookings/${bookingId}/check-in`, { method: 'POST' });
        // Update row status
        const statusEl = document.getElementById(`booking-status-${bookingId}`);
        if (statusEl) { statusEl.textContent = 'checked_in'; statusEl.className = 'badge-status active'; }
        const actionsEl = document.getElementById(`booking-actions-${bookingId}`);
        if (actionsEl) actionsEl.innerHTML = `
            <button onclick="adminCheckout('${bookingId}')"
                style="background:#059669;color:#fff;border:none;padding:4px 10px;border-radius:6px;cursor:pointer;font-size:12px;font-weight:600;">
                <i class="fa-solid fa-car-side"></i> Check-out</button>`;
        await loadParkingSpots();
    } catch(err) { alert('Check-in failed: ' + err.message); }
}

async function adminCheckout(bookingId) {
    try {
        await apiFetch(`/api/v1/bookings/${bookingId}/check-out`, { method: 'POST' });
        const statusEl = document.getElementById(`booking-status-${bookingId}`);
        if (statusEl) { statusEl.textContent = 'completed'; statusEl.className = 'badge-status available'; }
        const actionsEl = document.getElementById(`booking-actions-${bookingId}`);
        if (actionsEl) actionsEl.innerHTML = '—';
        await loadParkingSpots();
        await loadBookings();
    } catch(err) { alert('Check-out failed: ' + err.message); }
}

async function adminCancelBooking(bookingId, slotId) {
    if (!confirm(`Cancel booking ${bookingId}?\nSlot: ${slotId}`)) return;
    try {
        await apiFetch(`/api/v1/bookings/${bookingId}/cancel`, { method: 'POST' });
        const statusEl = document.getElementById(`booking-status-${bookingId}`);
        if (statusEl) { statusEl.textContent = 'cancelled'; statusEl.className = 'badge-status pending'; }
        const actionsEl = document.getElementById(`booking-actions-${bookingId}`);
        if (actionsEl) actionsEl.innerHTML = '—';

        // Release the slot
        const slotNumber = slotId.includes('_slot_') ? slotId.split('_slot_')[1] : slotId;
        await apiFetch(
            `/api/v1/iot/slot-update?parking_id=${PARKING_ID}&slot_number=${slotNumber}&status=available&device_key=${DEVICE_KEY}`,
            { method: 'POST' }
        ).catch(() => {});

        await loadParkingSpots();
        await loadBookings();
    } catch(err) { alert('Cancel failed: ' + err.message); }
}

function updatePaymentStats(bookings) {
    const total    = bookings.reduce((s, b) => s + Number(b.amount || b.total_amount || 0), 0);
    const pending  = bookings.filter(b => b.status === 'pending').reduce((s, b) => s + Number(b.amount || 0), 0);
    const success  = bookings.filter(b => b.status === 'completed').length;
    const rate     = bookings.length ? Math.round((success / bookings.length) * 100) : 0;

    const vals = document.querySelectorAll('.p-stat-value');
    if (vals[0]) vals[0].textContent = `${total.toFixed(2)} EGP`;
    if (vals[1]) vals[1].textContent = `${pending.toFixed(2)} EGP`;
    if (vals[2]) vals[2].textContent = bookings.length;
    if (vals[3]) vals[3].textContent = `${rate}%`;

    // analytics stats
    const aVals = document.querySelectorAll('.a-stat-value');
    if (aVals[0]) aVals[0].textContent = `${total.toFixed(0)} EGP`;
    if (aVals[1]) aVals[1].textContent = bookings.length;
}

// ════════════════════════════════════════════════════════════
// 8. ALERTS — /api/v1/admin/alerts
// ════════════════════════════════════════════════════════════
async function loadAlerts() {
    try {
        const data = await apiFetch('/api/v1/admin/alerts');
        if (!data) return;
        const alerts = data.data || data.alerts || data;

        // Store all IDs so polling doesn't re-show them as new
        alerts.forEach(a => {
            const id = a.id || a.alert_id || ((a.alert_type || a.type || 'alert') + '_' + a.created_at);
            lastAlertIds.add(id);
        });
        saveAlertIds();

        // Only count active alerts for stats
        const active = alerts.filter(a => (a.status || '').toLowerCase() === 'active');
        updateMonitoringStats(active);

    } catch (err) {
        console.error('Alerts error:', err);
    }
}

function renderDashboardAlerts() {
    const container = document.getElementById('alertsContainer');
    if (!container) return;

    const cached = cacheGet(CACHE.alerts);
    if (!cached || !cached.length) { container.innerHTML = ''; return; }

    // Show ONLY active alerts (not resolved/acknowledged), latest 3
    const active = cached
        .filter(a => (a.status || '').toLowerCase() === 'active')
        .slice(0, 3);

    if (!active.length) { container.innerHTML = ''; return; }

    container.innerHTML = active.map(alert => {
        const type  = (alert.alert_type || alert.type || 'info').toLowerCase();
        const colorMap = { fire: 'red', theft: 'red', weapon: 'red', security: 'orange', gate: 'yellow', info: 'blue' };
        const iconMap  = { fire: 'fa-fire', theft: 'fa-user-slash', weapon: 'fa-gun', security: 'fa-shield-halved', gate: 'fa-door-open', info: 'fa-circle-info' };
        const color = colorMap[type] || 'blue';
        const icon  = iconMap[type]  || 'fa-circle-exclamation';
        const time  = alert.created_at ? new Date(alert.created_at).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }) : '';
        const id    = alert.id || alert.alert_id || '';
        const labelMap = { fire: '🔥 Fire', theft: '🔫 Weapon/Theft', weapon: '🔫 Weapon', security: '⚠ Security', gate: '🚪 Gate' };
        const title = alert.title || labelMap[type] || type;

        return `
        <div class="alert-box alert-${color}" id="dashAlert-${id}">
            <i class="fa-solid ${icon}"></i>
            <div class="alert-content">
                <strong>${title}</strong>
                <p>${alert.message || alert.description || ''}</p>
                <small>${time}</small>
            </div>
            <button class="close-alert" onclick="dismissAlert('${id}', this)">
                <i class="fa-solid fa-xmark"></i>
            </button>
        </div>`;
    }).join('');
}

async function dismissAlert(alertId, btn) {
    const box = btn?.closest('.alert-box');
    if (box) box.remove();
    if (alertId) {
        await apiFetch(`/api/v1/admin/alerts/${alertId}/acknowledge`, { method: 'PUT' }).catch(() => {});
    }
}

function renderAlerts(alerts) {
    // Keep for compatibility — delegates to renderDashboardAlerts
    if (alerts) cacheSet(CACHE.alerts, alerts);
    renderDashboardAlerts();
}

// ════════════════════════════════════════════════════════════
// 9. NOTIFICATIONS — /api/v1/notifications
// ════════════════════════════════════════════════════════════
async function loadNotifications() {
    try {
        const data = await apiFetch('/api/v1/notifications');
        if (!data) return;

        const notifs = data.data || data.notifications || data;
        renderNotifications(notifs);

        // Unread count badge
        const unreadData = await apiFetch('/api/v1/notifications/unread-count').catch(() => null);
        if (unreadData) {
            const count = unreadData.count ?? unreadData.unread_count ?? 0;
            const badge = document.querySelector('.notification-icon .badge');
            if (badge) {
                badge.style.display = count > 0 ? '' : 'none';
                badge.textContent = count;
            }
        }

    } catch (err) {
        console.error('Notifications error:', err);
    }
}

function renderNotifications(notifs) {
    const container = document.getElementById('notificationsContainer');
    if (!container) return;

    // Get IDs already rendered (from storage) so we don't duplicate
    const existingIds = new Set(
        [...container.querySelectorAll('.notification-item')].map(el => el.dataset.id)
    );

    const typeIconMap  = { booking: 'fa-calendar-check', payment: 'fa-credit-card', alert: 'fa-bell', system: 'fa-gear', default: 'fa-bell' };
    const typeColorMap = { booking: 'blue-light', payment: 'green-light', alert: 'red-light', system: 'purple-light', default: 'blue-light' };

    // Only add notifs not already shown
    const toAdd = notifs.filter(n => {
        const id = String(n.id || n.notification_id || '');
        return id && !existingIds.has(id);
    });

    toAdd.forEach(n => {
        const type    = (n.type || 'default').toLowerCase();
        const icon    = typeIconMap[type]  || typeIconMap.default;
        const color   = typeColorMap[type] || typeColorMap.default;
        const isUnread = !n.is_read;
        const time     = n.created_at ? timeAgo(n.created_at) : '';
        const id       = n.id || n.notification_id;

        const div = document.createElement('div');
        div.className = `notification-item ${isUnread ? 'unread' : ''}`;
        div.dataset.id = id;
        div.innerHTML = `
            <div class="n-icon ${color}"><i class="fa-solid ${icon}"></i></div>
            <div class="n-content">
                <div class="n-title-row">
                    <h4>${n.title || 'Notification'} ${isUnread ? '<span class="unread-dot"></span>' : ''}</h4>
                </div>
                <p>${n.message || n.body || ''}</p>
                <span class="n-time">${time}</span>
            </div>
            <button class="n-delete-btn" data-id="${id}">
                <i class="fa-regular fa-trash-can"></i>
            </button>`;

        // Click to mark read
        if (isUnread) {
            div.addEventListener('click', async function () {
                await apiFetch(`/api/v1/notifications/${id}/read`, { method: 'PUT' }).catch(() => {});
                this.classList.remove('unread');
                this.querySelector('.unread-dot')?.remove();
                saveNotificationsToStorage();
            });
        }

        // Delete button
        div.querySelector('.n-delete-btn').addEventListener('click', async function(e) {
            e.stopPropagation();
            await apiFetch(`/api/v1/notifications/${id}`, { method: 'DELETE' }).catch(() => {});
            div.remove();
            saveNotificationsToStorage();
        });

        container.appendChild(div);
    });

    // Remove empty placeholder if we have items
    if (container.querySelectorAll('.notification-item').length > 0) {
        container.querySelector('.empty-msg')?.remove();
    }

    // Update unread badge
    const unreadCount = container.querySelectorAll('.notification-item.unread').length;
    const badge = document.querySelector('.notification-icon .badge');
    if (badge) {
        badge.textContent = unreadCount;
        badge.style.display = unreadCount > 0 ? '' : 'none';
    }

    // Mark all as read button
    const markAllBtn = document.querySelector('.flex-between a.text-blue');
    if (markAllBtn && !markAllBtn._bound) {
        markAllBtn._bound = true;
        markAllBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            await apiFetch('/api/v1/notifications/read-all', { method: 'PUT' }).catch(() => {});
            container.querySelectorAll('.notification-item.unread').forEach(item => {
                item.classList.remove('unread');
                item.querySelector('.unread-dot')?.remove();
            });
            if (badge) badge.style.display = 'none';
            saveNotificationsToStorage();
        });
    }
}

function timeAgo(dateStr) {
    const diff = Math.floor((Date.now() - new Date(dateStr)) / 1000);
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
}

// ════════════════════════════════════════════════════════════
// 10. DASHBOARD UI — Clocks, Nav, Modal, Pills
// ════════════════════════════════════════════════════════════
function initDashboardUI() {
    // Live clocks
    function updateClocks() {
        const t = new Date().toLocaleTimeString('en-US');
        document.querySelectorAll('.liveTime').forEach(el => el.textContent = t);
        const t24 = new Date().toLocaleTimeString('en-US', { hour12: false });
        document.querySelectorAll('.live-clock').forEach(el => el.textContent = t24);
    }
    updateClocks();
    setInterval(updateClocks, 1000);

    // Init charts
    initDashboardCharts();

    // Profile dropdown
    const profileBtn      = document.getElementById('userProfileBtn');
    const profileDropdown = document.getElementById('profileDropdown');
    if (profileBtn && profileDropdown) {
        profileBtn.addEventListener('click', e => { e.stopPropagation(); profileDropdown.classList.toggle('show'); });
        document.addEventListener('click', () => profileDropdown.classList.remove('show'));
    }

    // Mobile sidebar
    const mobileBtn      = document.getElementById('mobileMenuBtn');
    const sidebar        = document.getElementById('sidebar');
    const overlay        = document.getElementById('sidebarOverlay');
    const closeBtn       = document.getElementById('closeSidebarBtn');
    if (mobileBtn && sidebar && overlay) {
        const toggle = () => { sidebar.classList.toggle('open'); overlay.classList.toggle('show'); };
        mobileBtn.addEventListener('click', toggle);
        closeBtn?.addEventListener('click', toggle);
        overlay.addEventListener('click', toggle);
    }

    // Nav links (SPA navigation)
    const navLinks  = document.querySelectorAll('.sidebar-nav .nav-item[data-target]');
    const pageViews = document.querySelectorAll('.page-view');
    navLinks.forEach(link => {
        link.addEventListener('click', async (e) => {
            e.preventDefault();
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            pageViews.forEach(v => v.classList.remove('active'));
            const target = document.getElementById(link.dataset.target);
            if (target) target.classList.add('active');

            // Lazy-load section data
            const targetId = link.dataset.target;
            if (targetId === 'visitorsView')  await loadUsers();
            if (targetId === 'paymentsView')  await loadBookings();
            if (targetId === 'notificationsView') await loadNotifications();
            if (targetId === 'parkingSpotsView' || targetId === 'floorOverviewView') await loadParkingSpots();
            if (targetId === 'analyticsView') await loadAnalytics();

            if (window.innerWidth <= 768) {
                sidebar?.classList.remove('open');
                overlay?.classList.remove('show');
            }
        });
    });

    // Pills
    document.querySelectorAll('.pill').forEach(pill => {
        pill.addEventListener('click', function () {
            this.closest('.floor-filters')?.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // Spot filter buttons
    document.querySelectorAll('.spots-filters-bar .filter-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            this.closest('.filter-group')?.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            const filter = this.textContent.toLowerCase();
            document.querySelectorAll('.spot-box').forEach(box => {
                const status = (box.dataset.status || '').toLowerCase();
                box.style.display = (filter === 'all' || status === filter) ? '' : 'none';
            });
        });
    });

    // Payment filter buttons
    document.querySelectorAll('.table-filters-bar .filter-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            this.closest('.filter-group')?.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            const filter = this.textContent.toLowerCase();
            document.querySelectorAll('#paymentsTableBody tr').forEach(row => {
                const status = row.querySelector('.badge-status')?.textContent?.toLowerCase() || '';
                row.style.display = (filter === 'all' || status.includes(filter)) ? '' : 'none';
            });
        });
    });

    // Spot modal
    initSpotModal();
}

// Current open spot data
let currentSpot = {};

function switchTab(tab) {
    // Hide all tab contents
    ['Details', 'Edit', 'History'].forEach(t => {
        const content = document.getElementById(`tabContent${t}`);
        const btn     = document.getElementById(`tab${t}`);
        if (content) content.style.display = 'none';
        if (btn)     btn.classList.remove('active');
    });

    // Show selected
    const capTab = tab.charAt(0).toUpperCase() + tab.slice(1);
    const activeContent = document.getElementById(`tabContent${capTab}`);
    const activeBtn     = document.getElementById(`tab${capTab}`);
    if (activeContent) activeContent.style.display = '';
    if (activeBtn)     activeBtn.classList.add('active');

    if (tab === 'history') loadSpotHistory(currentSpot.id);
    if (tab === 'edit')    prefillEditForm();
}

function prefillEditForm() {
    const rate  = document.getElementById('editSpotRate');
    const type  = document.getElementById('editSpotType');
    const status= document.getElementById('editSpotStatus');
    if (rate)   rate.value   = currentSpot.hourly_rate || currentSpot.price_per_hour || 5;
    if (type)   type.value   = (currentSpot.spot_type  || 'standard').toLowerCase();
    if (status) status.value = (currentSpot.status     || 'available').toLowerCase();
}

function showModalMsg(elId, msg, isError = false) {
    const el = document.getElementById(elId);
    if (!el) return;
    el.textContent = msg;
    el.style.display = 'block';
    el.style.background = isError ? '#fee2e2' : '#d1fae5';
    el.style.color      = isError ? '#dc2626' : '#059669';
    setTimeout(() => { el.style.display = 'none'; }, 3000);
}

// Update modal buttons based on current spot status
function updateModalButtons(status) {
    const btnReserve     = document.getElementById('btnReserve');
    const btnCheckin     = document.getElementById('btnCheckin');
    const btnRelease     = document.getElementById('btnRelease');
    const btnMaintenance = document.getElementById('btnMaintenance');

    const s = (status || '').toLowerCase();

    // Reset reserve button to default style first
    if (btnReserve) {
        btnReserve.style.background = '';
        btnReserve.style.color      = '';
        btnReserve.style.border     = '';
        btnReserve.onclick = reserveCurrentSpot;
    }

    if (s === 'available') {
        if (btnReserve)     { btnReserve.style.display = ''; btnReserve.innerHTML = '<i class="fa-solid fa-lock"></i> Reserve Spot'; }
        if (btnCheckin)     { btnCheckin.style.display = ''; btnCheckin.innerHTML = '<i class="fa-solid fa-car-side"></i> Mark Occupied'; }
        if (btnRelease)       btnRelease.style.display = 'none';
        if (btnMaintenance) { btnMaintenance.style.display = ''; btnMaintenance.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> Mark Maintenance'; }

    } else if (s === 'reserved') {
        if (btnReserve)     {
            btnReserve.style.display    = '';
            btnReserve.style.background = '#dc2626';
            btnReserve.style.color      = '#fff';
            btnReserve.innerHTML        = '<i class="fa-solid fa-lock-open"></i> Unreserve';
            btnReserve.onclick          = unreserveCurrentSpot;
        }
        if (btnCheckin)     { btnCheckin.style.display = ''; btnCheckin.innerHTML = '<i class="fa-solid fa-car-side"></i> Mark Occupied'; }
        if (btnRelease)       btnRelease.style.display = 'none';
        if (btnMaintenance) { btnMaintenance.style.display = ''; btnMaintenance.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> Mark Maintenance'; }

    } else if (s === 'occupied') {
        if (btnReserve)     btnReserve.style.display = 'none';
        if (btnCheckin)     btnCheckin.style.display = 'none';
        if (btnRelease)     { btnRelease.style.display = ''; btnRelease.innerHTML = '<i class="fa-solid fa-lock-open"></i> Release Spot'; }
        if (btnMaintenance) { btnMaintenance.style.display = ''; btnMaintenance.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> Mark Maintenance'; }

    } else if (s === 'maintenance') {
        if (btnReserve)     btnReserve.style.display = 'none';
        if (btnCheckin)     btnCheckin.style.display = 'none';
        if (btnRelease)     { btnRelease.style.display = ''; btnRelease.innerHTML = '<i class="fa-solid fa-lock-open"></i> Release Spot'; }
        if (btnMaintenance) { btnMaintenance.style.display = ''; btnMaintenance.innerHTML = '<i class="fa-solid fa-rotate-left"></i> Unmark Maintenance'; }
    }
}

async function unreserveCurrentSpot() {
    if (!currentSpot.id) return;
    const btn = document.getElementById('btnReserve');
    if (btn) { btn.disabled = true; btn.textContent = 'Cancelling...'; }

    const slotNumber = currentSpot.id.includes('_slot_')
        ? currentSpot.id.split('_slot_')[1]
        : currentSpot.id;

    try {
        // Find active booking for this slot and cancel it
        const bookingsData = await apiFetch('/api/v1/admin/bookings').catch(() => null);
        if (bookingsData) {
            const bookings = bookingsData.data || bookingsData.bookings || bookingsData;
            const active   = bookings.find(b =>
                b.slot_id === currentSpot.id &&
                ['confirmed', 'reserved', 'active'].includes((b.status || '').toLowerCase())
            );
            if (active) {
                const bookingId = active.id || active.booking_id;
                await apiFetch(`/api/v1/bookings/${bookingId}/cancel`, { method: 'POST' }).catch(() => {});
            }
        }

        // Set slot back to available
        await apiFetch(
            `/api/v1/iot/slot-update?parking_id=${currentSpot.parking_id || PARKING_ID}&slot_number=${slotNumber}&status=available&device_key=${DEVICE_KEY}`,
            { method: 'POST' }
        );

        currentSpot.status = 'available';
        const statusEl = document.getElementById('modalSpotStatus');
        if (statusEl) { statusEl.textContent = 'available'; statusEl.className = 'badge-status available'; }
        showModalMsg('modalActionMsg', 'Reservation cancelled — Spot is now Available');
        updateModalButtons('available');
        await loadParkingSpots();
        initSpotModal();
    } catch(err) {
        showModalMsg('modalActionMsg', err.message || 'Failed to unreserve', true);
    }
    if (btn) { btn.disabled = false; }
}

async function checkinCurrentSpot() {
    if (!currentSpot.id) return;
    const btn = document.getElementById('btnCheckin');
    if (btn) btn.disabled = true;

    const slotNumber = currentSpot.id.includes('_slot_')
        ? currentSpot.id.split('_slot_')[1]
        : currentSpot.id;

    try {
        // Mark as occupied directly via IoT endpoint
        await apiFetch(
            `/api/v1/iot/slot-update?parking_id=${currentSpot.parking_id || PARKING_ID}&slot_number=${slotNumber}&status=occupied&device_key=${DEVICE_KEY}`,
            { method: 'POST' }
        );
        currentSpot.status = 'occupied';
        const statusEl = document.getElementById('modalSpotStatus');
        if (statusEl) { statusEl.textContent = 'occupied'; statusEl.className = 'badge-status occupied'; }
        showModalMsg('modalActionMsg', 'Spot marked as Occupied');
        updateModalButtons('occupied');
        await loadParkingSpots();
        initSpotModal();
    } catch(err) {
        showModalMsg('modalActionMsg', err.message || 'Failed', true);
    }
    if (btn) btn.disabled = false;
}

async function releaseCurrentSpot() {
    if (!currentSpot.id) return;
    const btn = document.getElementById('btnRelease');
    if (btn) { btn.disabled = true; btn.textContent = 'Releasing...'; }

    const slotNumber = currentSpot.id.includes('_slot_')
        ? currentSpot.id.split('_slot_')[1]
        : currentSpot.id;

    try {
        // Try check-out via bookings API first if there's an active booking
        const bookingsData = await apiFetch(`/api/v1/admin/bookings`).catch(() => null);
        if (bookingsData) {
            const bookings  = bookingsData.data || bookingsData.bookings || bookingsData;
            const active    = bookings.find(b =>
                b.slot_id === currentSpot.id &&
                ['active', 'confirmed', 'checked_in'].includes((b.status || '').toLowerCase())
            );
            if (active) {
                const bookingId = active.id || active.booking_id;
                await apiFetch(`/api/v1/bookings/${bookingId}/check-out`, { method: 'POST' }).catch(() => {});
            }
        }

        // Also set slot to available via IoT
        await apiFetch(
            `/api/v1/iot/slot-update?parking_id=${currentSpot.parking_id || PARKING_ID}&slot_number=${slotNumber}&status=available&device_key=${DEVICE_KEY}`,
            { method: 'POST' }
        );

        // Clear localStorage edit for this spot's status
        const saved = JSON.parse(localStorage.getItem('parkify_spot_edits') || '{}');
        if (saved[currentSpot.id]) {
            saved[currentSpot.id].status = 'available';
            localStorage.setItem('parkify_spot_edits', JSON.stringify(saved));
        }

        currentSpot.status = 'available';
        const statusEl = document.getElementById('modalSpotStatus');
        if (statusEl) { statusEl.textContent = 'available'; statusEl.className = 'badge-status available'; }
        showModalMsg('modalActionMsg', 'Spot released — now Available');
        updateModalButtons('available');
        await loadParkingSpots();
        initSpotModal();
    } catch(err) {
        showModalMsg('modalActionMsg', err.message || 'Failed to release', true);
    }
    if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fa-solid fa-lock-open"></i> Release Spot'; }
}

async function reserveCurrentSpot() {
    if (!currentSpot.id) return;

    // Show reserve form inline
    const msg = document.getElementById('modalActionMsg');
    if (msg) {
        msg.style.display = 'block';
        msg.style.background = '#eff6ff';
        msg.style.color = '#1d4ed8';
        msg.innerHTML = `
            <p style="margin:0 0 8px;font-weight:600;">Reserve Spot ${currentSpot.id}</p>
            <div style="display:grid;gap:8px;">
                <input id="reservePlate"  class="s-input" placeholder="Vehicle plate (e.g. ABC 123)" style="padding:8px;border:1px solid #d1d5db;border-radius:6px;">
                <input id="reserveHours"  class="s-input" type="number" value="1" min="1" max="24" placeholder="Duration (hours)" style="padding:8px;border:1px solid #d1d5db;border-radius:6px;">
                <button onclick="confirmReserve()" style="background:#6b21a8;color:#fff;border:none;padding:8px;border-radius:6px;cursor:pointer;font-weight:600;">Confirm Reserve</button>
            </div>`;
    }
}

async function confirmReserve() {
    const plate = document.getElementById('reservePlate')?.value.trim();
    const hours = parseFloat(document.getElementById('reserveHours')?.value) || 1;
    if (!plate) { showModalMsg('modalActionMsg', 'Please enter vehicle plate', true); return; }

    const btn = document.querySelector('#modalActionMsg button');
    if (btn) { btn.disabled = true; btn.textContent = 'Reserving...'; }

    const now = new Date();
    const end = new Date(now.getTime() + hours * 3600000);

    const slotId = currentSpot.id.includes('_slot_')
        ? currentSpot.id
        : `${currentSpot.parking_id || PARKING_ID}_slot_${currentSpot.id}`;

    try {
        const result = await apiFetch('/api/v1/bookings', {
            method: 'POST',
            body: JSON.stringify({
                parking_id:     currentSpot.parking_id || PARKING_ID,
                slot_id:        slotId,
                vehicle_plate:  plate,
                start_time:     now.toISOString(),
                end_time:       end.toISOString(),
                payment_method: 'cash'
            })
        });

        if (!result) return; // redirected to login

        currentSpot.status = 'reserved';
        const statusEl = document.getElementById('modalSpotStatus');
        if (statusEl) { statusEl.textContent = 'reserved'; statusEl.className = 'badge-status reserved'; }
        updateModalButtons('reserved');
        showModalMsg('modalActionMsg', `Spot reserved for ${hours}h ✅`);
        await loadParkingSpots();
        initSpotModal();
    } catch(err) {
        // Token expired?
        if (err.message && (err.message.includes('authenticated') || err.message.includes('token') || err.message.includes('expired'))) {
            showModalMsg('modalActionMsg', 'Session expired — please log in again', true);
            setTimeout(() => { clearAuth(); window.location.href = 'login.html'; }, 1500);
        } else {
            showModalMsg('modalActionMsg', err.message || 'Failed to reserve', true);
        }
        if (btn) btn.disabled = false;
    }
}

async function markMaintenanceSpot() {
    if (!currentSpot.id) return;
    const btn = document.getElementById('btnMaintenance');
    btn.disabled = true;

    // Toggle: if already maintenance → set available, else → set maintenance
    const newStatus  = currentSpot.status === 'maintenance' ? 'available' : 'maintenance';
    const slotNumber = currentSpot.id.includes('_slot_')
        ? currentSpot.id.split('_slot_')[1]
        : currentSpot.id;

    try {
        await apiFetch(
            `/api/v1/iot/slot-update?parking_id=${currentSpot.parking_id || PARKING_ID}&slot_number=${slotNumber}&status=${newStatus}&device_key=${DEVICE_KEY}`,
            { method: 'POST' }
        );
        showModalMsg('modalActionMsg', `Spot marked as ${newStatus}`);

        // Save to localStorage
        const saved = JSON.parse(localStorage.getItem('parkify_spot_edits') || '{}');
        saved[currentSpot.id] = { ...(saved[currentSpot.id] || {}), status: newStatus };
        localStorage.setItem('parkify_spot_edits', JSON.stringify(saved));

        currentSpot.status = newStatus;
        const statusEl = document.getElementById('modalSpotStatus');
        if (statusEl) { statusEl.textContent = newStatus; statusEl.className = `badge-status ${newStatus}`; }

        // Update button label
        btn.innerHTML = newStatus === 'maintenance'
            ? '<i class="fa-solid fa-triangle-exclamation"></i> Unmark Maintenance'
            : '<i class="fa-solid fa-triangle-exclamation"></i> Mark Maintenance';

        await loadParkingSpots();
        initSpotModal();
    } catch(err) {
        showModalMsg('modalActionMsg', err.message || 'Failed', true);
    }
    btn.disabled = false;
}

async function deleteCurrentSpot() {
    if (!currentSpot.id) return;
    if (!confirm(`Delete spot ${currentSpot.id.includes('_slot_') ? currentSpot.id.split('_slot_')[1] : currentSpot.id}?`)) return;

    const slotNumber = currentSpot.id.includes('_slot_')
        ? currentSpot.id.split('_slot_')[1]
        : currentSpot.id;

    try {
        // Try to notify backend — but don't fail if it errors
        await apiFetch(
            `/api/v1/iot/slot-update?parking_id=${currentSpot.parking_id || PARKING_ID}&slot_number=${slotNumber}&status=maintenance&device_key=${DEVICE_KEY}`,
            { method: 'POST' }
        ).catch(() => {});

        // Remove from localStorage
        const saved = JSON.parse(localStorage.getItem('parkify_spot_edits') || '{}');
        delete saved[currentSpot.id];
        localStorage.setItem('parkify_spot_edits', JSON.stringify(saved));

        // Remove from HTML_SLOT_IDS so it's no longer tracked
        HTML_SLOT_IDS.delete(currentSpot.id);

        // Remove the spot box from grid immediately — no refresh needed
        const box = document.querySelector(`.spot-box[data-id="${currentSpot.id}"]`);
        if (box) box.remove();

        // Close modal
        const modal = document.getElementById('spotDetailsModal');
        if (modal) modal.classList.remove('show');

        // Update stats
        const remaining = Array.from(document.querySelectorAll('.spot-box'));
        const counts = { available: 0, occupied: 0, reserved: 0, maintenance: 0 };
        remaining.forEach(b => {
            const st = (b.dataset.status || '').toLowerCase();
            if (counts[st] !== undefined) counts[st]++;
        });
        const totalEl = document.querySelector('.spot-stat-card .stat-num');
        if (totalEl) totalEl.textContent = remaining.length;

    } catch(err) {
        showModalMsg('modalActionMsg', err.message || 'Failed to delete', true);
    }
}

async function saveSpotEdit() {
    if (!currentSpot.id) return;
    const rate   = parseFloat(document.getElementById('editSpotRate')?.value) || 5;
    const type   = document.getElementById('editSpotType')?.value  || 'standard';
    const status = document.getElementById('editSpotStatus')?.value || 'available';

    const slotNumber = currentSpot.id.includes('_slot_')
        ? currentSpot.id.split('_slot_')[1]
        : currentSpot.id;

    try {
        // Update status via IoT if changed
        if (status !== currentSpot.status) {
            await apiFetch(
                `/api/v1/iot/slot-update?parking_id=${currentSpot.parking_id || PARKING_ID}&slot_number=${slotNumber}&status=${status}&device_key=${DEVICE_KEY}`,
                { method: 'POST' }
            );
        }

        // Save all edits to localStorage
        const saved = JSON.parse(localStorage.getItem('parkify_spot_edits') || '{}');
        saved[currentSpot.id] = { hourly_rate: rate, spot_type: type, status };
        localStorage.setItem('parkify_spot_edits', JSON.stringify(saved));

        currentSpot.hourly_rate = rate;
        currentSpot.spot_type   = type;
        currentSpot.status      = status;

        showModalMsg('editActionMsg', 'Changes saved!');

        const rateEl = document.getElementById('infoSpotRate');
        if (rateEl) rateEl.textContent = `${rate} EGP/hour`;
        const typeEl = document.getElementById('infoSpotType');
        if (typeEl) typeEl.textContent = type.charAt(0).toUpperCase() + type.slice(1);

        await loadParkingSpots();
        initSpotModal();
        setTimeout(() => switchTab('details'), 1200);
    } catch(err) {
        showModalMsg('editActionMsg', err.message || 'Failed to save', true);
    }
}

async function loadSpotHistory(spotId) {
    const container = document.getElementById('spotBookingHistory');
    if (!container || !spotId) return;
    container.innerHTML = '<p style="color:#6b7280;font-size:14px;">Loading...</p>';
    try {
        const data = await apiFetch(`/api/v1/admin/bookings?slot_id=${spotId}`);
        const bookings = data?.data || data?.bookings || data || [];
        if (!bookings.length) {
            container.innerHTML = '<p style="color:#6b7280;font-size:14px;">No booking history for this spot.</p>';
            return;
        }
        container.innerHTML = bookings.slice(0, 10).map(b => {
            const date   = b.created_at ? new Date(b.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '--';
            const status = b.status || 'unknown';
            const cls    = status === 'completed' ? 'available' : status === 'active' ? 'active' : 'pending';
            return `
            <div style="display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid #f3f4f6;">
                <div>
                    <strong style="font-size:13px;">${b.user_name || b.user?.username || 'User'}</strong>
                    <div style="font-size:12px;color:#6b7280;">${date}</div>
                </div>
                <div style="text-align:right;">
                    <span class="badge-status ${cls}">${status}</span>
                    <div style="font-size:12px;color:#6b7280;margin-top:2px;">${Number(b.amount || 0).toFixed(2)} EGP</div>
                </div>
            </div>`;
        }).join('');
    } catch(err) {
        container.innerHTML = '<p style="color:#6b7280;font-size:14px;">Could not load history.</p>';
    }
}

function initSpotModal() {
    const modalOverlay  = document.getElementById('spotDetailsModal');
    const closeModalBtns = [document.getElementById('closeModalBtn'), document.getElementById('closeModalFooterBtn')];
    const savedEdits    = JSON.parse(localStorage.getItem('parkify_spot_edits') || '{}');

    document.querySelectorAll('.spot-box').forEach(box => {
        // Remove old listener to avoid duplicates
        const newBox = box.cloneNode(true);
        box.parentNode.replaceChild(newBox, box);

        newBox.addEventListener('click', function () {
            const spotId = this.dataset.id;
            const status = (this.dataset.status || 'available').toLowerCase();

            // Build spot object from data attrs + any saved edits
            const edit = savedEdits[spotId] || {};
            currentSpot = {
                id:          spotId,
                parking_id:  this.dataset.parkingId || 'parking_1',
                status:      edit.status || status,
                hourly_rate: edit.hourly_rate || 5,
                spot_type:   edit.spot_type   || 'standard'
            };

            // Update modal header
            const displayId = spotId.includes('_slot_') ? spotId.split('_slot_')[1] : spotId;
            const spotIdEl = document.getElementById('modalSpotId');
            if (spotIdEl) spotIdEl.textContent = displayId;
            const infoIdEl = document.getElementById('infoSpotId');
            if (infoIdEl) infoIdEl.textContent = displayId;

            const statusEl = document.getElementById('modalSpotStatus');
            if (statusEl) {
                statusEl.textContent  = currentSpot.status;
                statusEl.className    = `badge-status ${currentSpot.status}`;
            }

            // Rate & type
            const rateEl = document.getElementById('infoSpotRate');
            if (rateEl) rateEl.textContent = `${currentSpot.hourly_rate} EGP/hour`;
            const typeEl = document.getElementById('infoSpotType');
            if (typeEl) typeEl.textContent = currentSpot.spot_type.charAt(0).toUpperCase() + currentSpot.spot_type.slice(1);

            // Icon color
            const iconEl = document.querySelector('.modal-icon');
            if (iconEl) {
                const colorMap = { available: ['#ecfdf5','#059669'], occupied: ['#fee2e2','#dc2626'], reserved: ['#fffbeb','#d97706'], maintenance: ['#f3f4f6','#4b5563'] };
                const [bg, color] = colorMap[currentSpot.status] || ['#f3f4f6','#4b5563'];
                iconEl.style.background = bg;
                iconEl.style.color      = color;
            }

            // Update all action buttons based on status
            updateModalButtons(currentSpot.status);

            // Reset to details tab
            switchTab('details');
            modalOverlay?.classList.add('show');
        });
    });

    const closeModal = () => {
        modalOverlay?.classList.remove('show');
        switchTab('details');
    };
    closeModalBtns.forEach(btn => btn?.addEventListener('click', closeModal));
    modalOverlay?.addEventListener('click', e => { if (e.target === modalOverlay) closeModal(); });
}

// ════════════════════════════════════════════════════════════
// 11. ANALYTICS (basic placeholder with real booking data)
// ════════════════════════════════════════════════════════════
async function loadAnalytics() {
    // Analytics data comes from the bookings data already loaded
    // If Chart.js is available, we can render charts
    if (typeof Chart === 'undefined') return;

    try {
        const data = await apiFetch('/api/v1/admin/bookings');
        if (!data) return;
        const bookings = data.data || data.bookings || data;

        // Group by day for revenue trend
        const dayMap = {};
        bookings.forEach(b => {
            const day = b.created_at ? new Date(b.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : 'Unknown';
            if (!dayMap[day]) dayMap[day] = { revenue: 0, count: 0 };
            dayMap[day].revenue += Number(b.amount || 0);
            dayMap[day].count++;
        });

        const labels   = Object.keys(dayMap).slice(-7);
        const revenues = labels.map(l => dayMap[l].revenue);
        const counts   = labels.map(l => dayMap[l].count);

        const revCanvas = document.getElementById('revenueTrendChart');
        if (revCanvas) {
            new Chart(revCanvas, {
                type: 'line',
                data: {
                    labels,
                    datasets: [
                        { label: 'Revenue (EGP)', data: revenues, borderColor: '#7c3aed', backgroundColor: 'rgba(124,58,237,0.1)', tension: 0.4, fill: true },
                        { label: 'Bookings', data: counts, borderColor: '#06b6d4', backgroundColor: 'rgba(6,182,212,0.1)', tension: 0.4, fill: true, yAxisID: 'y2' }
                    ]
                },
                options: { responsive: true, scales: { y: { beginAtZero: true }, y2: { position: 'right', beginAtZero: true } } }
            });
        }
    } catch (err) {
        console.error('Analytics error:', err);
    }
}

// ════════════════════════════════════════════════════════════
// 13. AI CAMERA CONNECTION + FULLSCREEN MODAL
// ════════════════════════════════════════════════════════════

const CAM_URL = 'http://127.0.0.1:5000/video_feed';

// Open camera fullscreen
function openCameraModal() {
    const modal       = document.getElementById('cameraModal');
    const modalStream = document.getElementById('modalCamStream');
    const alertBadge  = document.getElementById('modalAlertBadge');
    if (!modal) return;

    modalStream.src   = CAM_URL;
    modal.style.display = 'flex';

    // Show badge if alert is active
    const overlay = document.getElementById('aiAlertOverlay');
    if (overlay && overlay.style.display !== 'none') {
        alertBadge.style.display = 'block';
    }

    // Close on Escape key
    document.onkeydown = (e) => { if (e.key === 'Escape') closeCameraModal(); };
}

function closeCameraModal() {
    const modal       = document.getElementById('cameraModal');
    const modalStream = document.getElementById('modalCamStream');
    if (!modal) return;
    modal.style.display = 'none';
    modalStream.src = ''; // Stop stream to save resources
    document.onkeydown = null;
}

function initAICamera() {
    const img      = document.getElementById('aiCameraStream');
    const offline  = document.getElementById('aiCameraOffline');
    const statusEl = document.getElementById('aiCameraStatus');
    const nameEl   = document.getElementById('aiCameraName');
    const msgEl    = document.getElementById('aiCameraMsg');
    if (!img) return;

    // Already connected — don't reset
    if (img.src && img.src.includes('video_feed') && img.style.display !== 'none') return;

    function connect() {
        img.src           = CAM_URL;
        img.style.display = 'block';
        if (offline) offline.style.display = 'none';
        if (statusEl) { statusEl.textContent = 'Online'; statusEl.className = 'cam-status active'; }
        if (nameEl)   nameEl.textContent = 'AI Cam — Ground Floor';

        img.onerror = () => {
            img.style.display = 'none';
            if (offline) offline.style.display = 'flex';
            if (statusEl) { statusEl.textContent = 'Offline'; statusEl.className = 'cam-status inactive'; }
            if (msgEl)    msgEl.textContent = 'ai_camera.py offline — retrying in 5s';
            setTimeout(connect, 5000);
        };

        const camCount    = document.querySelector('.cam-count');
        const statCameras = document.getElementById('statCameras');
        if (camCount)    camCount.textContent    = '1';
        if (statCameras) statCameras.textContent = '1';
    }

    connect();
}

// ════════════════════════════════════════════════════════════
// 14. REAL-TIME ALERTS POLLING (AI Camera Integration)
// ════════════════════════════════════════════════════════════

// Persist alert IDs across page refreshes
let lastAlertIds   = new Set(JSON.parse(localStorage.getItem('parkify_seen_alert_ids') || '[]'));
let lastAlertCount = 0;
let alertPollingTimer = null;
// Timestamp when dashboard was opened — only show alerts newer than this
const DASHBOARD_START_TIME = new Date();

function saveAlertIds() {
    localStorage.setItem('parkify_seen_alert_ids', JSON.stringify([...lastAlertIds]));
}

// Track active emergency IDs separately from notification IDs
let activeEmergencyIds = new Set();
let bannerTimer = null;

async function pollAlertsRealtime() {
    try {
        const data = await apiFetch('/api/v1/admin/alerts');
        if (!data) return;

        const alerts = data.data || data.alerts || data;
        if (!Array.isArray(alerts)) return;

        // 1. New alerts — only show if:
        //    a) Not seen before (by ID)
        //    b) Status is 'active' (not acknowledged/resolved)
        //    c) Created AFTER the dashboard was opened
        const newAlerts = alerts.filter(a => {
            const id     = a.id || a.alert_id || ((a.alert_type || a.type || 'alert') + '_' + a.created_at);
            const status = (a.status || '').toLowerCase();

            if (lastAlertIds.has(id)) return false;
            lastAlertIds.add(id);

            // Skip non-active alerts (acknowledged, resolved, etc.)
            if (status && status !== 'active') return false;

            // Skip old alerts from before dashboard opened
            if (a.created_at) {
                const alertTime = new Date(a.created_at);
                if (alertTime < DASHBOARD_START_TIME) return false;
            }
            return true;
        });
        saveAlertIds();

        if (newAlerts.length > 0) {
            newAlerts.forEach(alert => {
                showRealtimeAlert(alert);
                addRealtimeNotification(alert);
                const t = (alert.alert_type || alert.type || '').toLowerCase();
                if (['fire','theft','weapon','security'].includes(t)) {
                    triggerCameraAlertOverlay(alert);
                }
            });
        }

        // 2. Emergency banner — active fire/theft/weapon alerts
        const currentEmergency = alerts.filter(a =>
            ['fire','theft','weapon'].includes((a.alert_type || a.type || '').toLowerCase()) &&
            (a.status || '').toLowerCase() === 'active'
        );

        const badge  = document.getElementById('emergencyBadge');
        const banner = document.getElementById('emergencyBanner');
        const list   = document.getElementById('emergencyList');

        if (currentEmergency.length > 0) {
            const latest    = currentEmergency[0];
            const alertType = (latest.alert_type || latest.type || '').toLowerCase();
            const labelMap  = { fire: '🔥 Fire Detected', theft: '⚠ Weapon / Theft Detected', weapon: '⚠ Weapon Detected' };
            const label     = latest.title || labelMap[alertType] || alertType;

            if (badge) { badge.style.display = ''; badge.querySelector('span').textContent = currentEmergency.length; }
            if (banner) { banner.style.display = ''; if (list) list.innerHTML = `<span>${label}</span>`; }
            if (bannerTimer) { clearTimeout(bannerTimer); bannerTimer = null; }

        } else {
            if (badge) badge.style.display = 'none';
            if (banner && banner.style.display !== 'none' && !bannerTimer) {
                bannerTimer = setTimeout(() => {
                    if (banner) banner.style.display = 'none';
                    bannerTimer = null;
                }, 5000);
            }
        }

        // Update stats with all active alerts
        updateMonitoringStats(alerts);

    } catch (err) {
        // Silent fail
    }
}

function showRealtimeAlert(alert) {
    const container = document.getElementById('alertsContainer');
    if (!container) return;

    const type     = (alert.alert_type || alert.type || 'info').toLowerCase();
    const colorMap = { fire: 'red', theft: 'red', weapon: 'red', security: 'orange', low_capacity: 'yellow', info: 'blue' };
    const iconMap  = { fire: 'fa-fire', theft: 'fa-user-slash', weapon: 'fa-gun', security: 'fa-shield-halved', low_capacity: 'fa-parking', info: 'fa-circle-info' };
    const color    = colorMap[type] || 'blue';
    const icon     = iconMap[type]  || 'fa-circle-exclamation';
    const time     = alert.created_at ? new Date(alert.created_at).toLocaleTimeString() : 'Just now';
    const id       = alert.id || alert.alert_id || Date.now();

    // Remove existing alert with same ID
    document.getElementById(`alert-${id}`)?.remove();

    const div = document.createElement('div');
    div.className = `alert-box alert-${color}`;
    div.id = `alert-${id}`;
    div.style.cssText = 'animation: slideIn 0.3s ease;';
    div.innerHTML = `
        <i class="fa-solid ${icon}"></i>
        <div class="alert-content">
            <strong>${alert.title || alert.alert_type || alert.type || 'Alert'}</strong>
            <p>${alert.message || alert.description || ''}</p>
            <small>${time}</small>
        </div>
        <button class="close-alert" onclick="this.closest('.alert-box').remove()">
            <i class="fa-solid fa-xmark"></i>
        </button>`;

    // Prepend new alert
    container.prepend(div);

    // Keep max 5 alerts visible
    const allAlerts = container.querySelectorAll('.alert-box');
    if (allAlerts.length > 5) allAlerts[allAlerts.length - 1].remove();
}

function saveNotificationsToStorage() {
    const container = document.getElementById('notificationsContainer');
    if (!container) return;
    const items = [];
    container.querySelectorAll('.notification-item').forEach(item => {
        items.push({
            id:      item.id,
            html:    item.innerHTML,
            unread:  item.classList.contains('unread')
        });
    });
    localStorage.setItem('parkify_notifications', JSON.stringify(items));
}

function loadNotificationsFromStorage() {
    const container = document.getElementById('notificationsContainer');
    if (!container) return;
    const saved = JSON.parse(localStorage.getItem('parkify_notifications') || '[]');
    if (!saved.length) return;

    // Clear default "No notifications" placeholder
    container.innerHTML = '';
    saved.forEach(item => {
        const div = document.createElement('div');
        div.className = 'notification-item' + (item.unread ? ' unread' : '');
        div.id = item.id;
        div.innerHTML = item.html;
        // Re-attach delete button handler
        const btn = div.querySelector('.n-delete-btn');
        if (btn) btn.onclick = () => {
            div.remove();
            saveNotificationsToStorage();
        };
        container.appendChild(div);
    });

    // Update badge
    const unreadCount = saved.filter(i => i.unread).length;
    const badge = document.querySelector('.notification-icon .badge');
    if (badge && unreadCount > 0) {
        badge.textContent = unreadCount;
        badge.style.display = '';
    }
}

function addRealtimeNotification(alert) {
    const container = document.getElementById('notificationsContainer');
    if (!container) return;

    const type     = (alert.alert_type || alert.type || 'info').toLowerCase();
    const iconMap  = { fire: 'fa-fire', theft: 'fa-user-slash', weapon: 'fa-gun', security: 'fa-shield-halved', default: 'fa-bell' };
    const colorMap = { fire: 'red-light', theft: 'red-light', weapon: 'red-light', security: 'orange-light', default: 'blue-light' };
    const icon     = iconMap[type]  || iconMap.default;
    const color    = colorMap[type] || colorMap.default;
    const id       = alert.id || alert.alert_id || Date.now();
    const time     = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

    // Remove "No notifications" message if present
    const empty = container.querySelector('.empty-msg');
    if (empty) empty.remove();

    const div = document.createElement('div');
    div.className = 'notification-item unread';
    div.id = `notif-alert-${id}`;
    div.innerHTML = `
        <div class="n-icon ${color}"><i class="fa-solid ${icon}"></i></div>
        <div class="n-content">
            <div class="n-title-row">
                <h4>${alert.title || alert.alert_type || alert.type || 'Alert'} <span class="unread-dot"></span></h4>
            </div>
            <p>${alert.message || alert.description || 'AI Camera detected an event'}</p>
            <span class="n-time">${time}</span>
        </div>
        <button class="n-delete-btn"><i class="fa-regular fa-trash-can"></i></button>`;

    div.querySelector('.n-delete-btn').onclick = () => {
        div.remove();
        saveNotificationsToStorage();
    };

    container.prepend(div);
    saveNotificationsToStorage();

    // Update unread badge
    const badge = document.querySelector('.notification-icon .badge');
    if (badge) {
        const current = parseInt(badge.textContent) || 0;
        badge.textContent = current + 1;
        badge.style.display = '';
    }
}

function triggerCameraAlertOverlay(alert) {
    const overlay = document.getElementById('aiAlertOverlay');
    const label   = document.getElementById('aiAlertLabel');
    if (!overlay || !label) return;

    const type    = (alert.alert_type || alert.type || '').toLowerCase();
    const labelMap = {
        fire:     { text: '🔥 FIRE DETECTED',   color: '#f97316' },
        theft:    { text: '🔫 WEAPON / THEFT',   color: '#ef4444' },
        weapon:   { text: '🔫 WEAPON DETECTED',  color: '#ef4444' },
        security: { text: '⚠ SECURITY BREACH',  color: '#dc2626' },
    };
    const cfg = labelMap[type] || { text: '⚠ ALERT', color: '#ef4444' };

    overlay.style.display     = 'block';
    overlay.style.borderColor = cfg.color;
    label.style.background    = cfg.color;
    label.textContent         = cfg.text;

    setTimeout(() => { overlay.style.display = 'none'; }, 8000);
}

function saveStatsToStorage(total, fire, security) {
    localStorage.setItem('parkify_stats', JSON.stringify({ total, fire, security, ts: Date.now() }));
}

function loadStatsFromStorage() {
    try {
        const saved = JSON.parse(localStorage.getItem('parkify_stats') || 'null');
        if (!saved) return;
        const monStats = document.querySelectorAll('#monitoringStats .stat-value');
        if (monStats[1]) monStats[1].textContent = saved.total;
        if (monStats[2]) monStats[2].textContent = saved.fire;
        if (monStats[3]) monStats[3].textContent = saved.security;
    } catch(e) {}
}

function loadSpotStatsFromStorage() {
    try {
        const s = JSON.parse(localStorage.getItem('parkify_spot_stats') || 'null');
        if (!s) return;

        // Dashboard main cards
        const statAvailable = document.getElementById('statAvailable');
        if (statAvailable) statAvailable.innerHTML = `${s.available ?? 0} <span class="stat-sub">/ ${s.total ?? 0}</span>`;
        const statOccupancy = document.getElementById('statOccupancy');
        if (statOccupancy) statOccupancy.innerHTML = `${s.occ ?? 0}% <span class="stat-sub">Overall</span>`;

        // Sidebar
        const progressFill = document.querySelector('.progress-fill');
        const progressText = document.querySelector('.progress-text');
        if (progressFill) progressFill.style.width = `${s.occ ?? 0}%`;
        if (progressText) progressText.textContent  = `${s.occ ?? 0}%`;

        // Spots stats grid
        const statNums = document.querySelectorAll('.spot-stat-card .stat-num');
        if (statNums[0]) statNums[0].textContent = s.total ?? 0;
        if (statNums[1]) statNums[1].textContent = s.available ?? 0;
        if (statNums[2]) statNums[2].textContent = s.occupied ?? 0;
        if (statNums[3]) statNums[3].textContent = s.reserved ?? 0;
        if (statNums[4]) statNums[4].textContent = s.maintenance ?? 0;
    } catch(e) {}
}

function updateMonitoringStats(alerts) {
    // Only count active alerts (real-time only — no persisted data)
    const active   = (alerts || []).filter(a => (a.status || '').toLowerCase() === 'active');
    const fire     = active.filter(a => (a.alert_type || a.type || '').toLowerCase() === 'fire').length;
    const security = active.filter(a => ['theft', 'weapon', 'security'].includes((a.alert_type || a.type || '').toLowerCase())).length;
    const total    = active.length;

    const monStats = document.querySelectorAll('#monitoringStats .stat-value');
    if (monStats[1]) monStats[1].textContent = total;
    if (monStats[2]) monStats[2].textContent = fire;
    if (monStats[3]) monStats[3].textContent = security;

    saveStatsToStorage(total, fire, security);

    const modalBadge = document.getElementById('modalAlertBadge');
    if (modalBadge) modalBadge.style.display = (fire + security) > 0 ? 'block' : 'none';
}

// Track previous slot statuses to detect changes from app bookings
let prevSlotStatuses = {};

async function pollSpotsRealtime() {
    try {
        const slotsData = await apiFetch(`/api/v1/admin/parkings/${currentParkingId || PARKING_ID}/slots`);
        if (!slotsData) return;

        const allSlots = slotsData.data || slotsData.slots || slotsData;
        if (!Array.isArray(allSlots)) return;
        const slots = filterMySlots(allSlots);

        // Build slot map — handle undefined slot_id
        const slotMap = {};
        slots.forEach(s => {
            const slotNum = s.slot_number || '';
            const id = s.slot_id || s.id ||
                (slotNum ? `parking_1_slot_${slotNum}` : null);
            if (id) slotMap[id] = s;
            if (slotNum) slotMap[slotNum] = s;
        });

        // Check for changes and update only changed spots
        let changed = false;
        slots.forEach(s => {
            const slotNum = s.slot_number || '';
            const id = s.slot_id || s.id || (slotNum ? `parking_1_slot_${slotNum}` : null);
            if (!id) return;
            const status = (s.status || '').toLowerCase();
            if (prevSlotStatuses[id] !== undefined && prevSlotStatuses[id] !== status) {
                changed = true;
                const box = document.querySelector(`.spot-box[data-id="${id}"]`);
                if (box) {
                    const statusMap = { available: 'free', occupied: 'taken', reserved: 'reserved', maintenance: 'maintenance' };
                    box.className = `spot-box ${statusMap[status] || 'free'}`;
                    box.dataset.status = status.charAt(0).toUpperCase() + status.slice(1);
                    const footerEl = box.querySelector('.spot-footer');
                    if (footerEl) footerEl.textContent = status.charAt(0).toUpperCase() + status.slice(1);
                }
            }
            prevSlotStatuses[id] = status;
        });

        if (changed) {
            cacheSet(CACHE.slots, slots);
            updateSpotStats(slots);
            // No initSpotModal() here — avoids shake
        }

        // Always check if open modal needs updating
        const modalOverlay = document.getElementById('spotDetailsModal');
        const modalIsOpen  = modalOverlay && modalOverlay.classList.contains('show');

        if (modalIsOpen && currentSpot.id) {
            const updatedSlot = slotMap[currentSpot.id];
            if (updatedSlot) {
                const newStatus = (updatedSlot.status || '').toLowerCase();
                if (newStatus !== currentSpot.status) {
                    currentSpot.status = newStatus;
                    const statusEl = document.getElementById('modalSpotStatus');
                    if (statusEl) { statusEl.textContent = newStatus; statusEl.className = `badge-status ${newStatus}`; }
                    const iconEl = document.querySelector('.modal-icon');
                    if (iconEl) {
                        const colorMap = { available: ['#ecfdf5','#059669'], occupied: ['#fee2e2','#dc2626'], reserved: ['#fffbeb','#d97706'], maintenance: ['#f3f4f6','#4b5563'] };
                        const [bg, color] = colorMap[newStatus] || ['#f3f4f6','#4b5563'];
                        iconEl.style.background = bg;
                        iconEl.style.color = color;
                    }
                    updateModalButtons(newStatus);
                }
            }
        }

    } catch(err) {
        // Silent fail
    }
}

function startAlertsPolling() {
    // First check immediately
    pollAlertsRealtime();
    pollSpotsRealtime();

    // Alerts every 5 seconds
    alertPollingTimer = setInterval(pollAlertsRealtime, 5000);
    // Spots every 5 seconds — catches bookings from app
    setInterval(pollSpotsRealtime, 5000);
}

// ════════════════════════════════════════════════════════════
// 12. INIT — Entry Point
// ════════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', async () => {
    initPasswordToggle();

    // Auth pages
    initRegister();
    initLogin();

    // Dashboard pages
    if (document.querySelector('.dashboard-page')) {
        if (!guardDashboard()) return;

        initProfileDisplay();
        initDashboardUI();

        // Clear old alerts cache and stats on startup — real-time only
        localStorage.removeItem(CACHE.alerts);
        localStorage.removeItem('parkify_stats');
        const _startBanner = document.getElementById('emergencyBanner');
        const _startBadge  = document.getElementById('emergencyBadge');
        if (_startBanner) _startBanner.style.display = 'none';
        if (_startBadge)  _startBadge.style.display  = 'none';

        // Reset monitoring stats to 0
        const _monStats = document.querySelectorAll('#monitoringStats .stat-value');
        if (_monStats[1]) _monStats[1].textContent = '0';
        if (_monStats[2]) _monStats[2].textContent = '0';
        if (_monStats[3]) _monStats[3].textContent = '0';

        // Load persisted data instantly before API calls
        loadNotificationsFromStorage();
        loadStatsFromStorage();
        loadSpotStatsFromStorage();

        // Then load from API
        await Promise.allSettled([
            loadDashboardStats(),
            loadParkingSpots(),
            loadAlerts(),
            loadNotifications()
        ]);

        // Start camera and real-time polling
        initAICamera();
        startAlertsPolling();

        // Dashboard auto-refresh every 10 seconds
        setInterval(async () => {
            await loadDashboardStats();
            await loadAlerts();
            await loadBookings(); // keeps revenue up to date
        }, 10000);
    }
});

// ════════════════════════════════════════════════════════════
// ADD SPOT
// ════════════════════════════════════════════════════════════
function openAddSpotModal() {
    const modal = document.getElementById('addSpotModal');
    if (modal) {
        modal.style.display = 'flex';
        document.getElementById('newSpotNumber').value = '';
        document.getElementById('addSpotMsg').style.display = 'none';
    }
}

function closeAddSpotModal() {
    const modal = document.getElementById('addSpotModal');
    if (modal) modal.style.display = 'none';
    document.getElementById('addSpotMsg').style.display = 'none';
    document.getElementById('newSpotNumber').value = '';
}

async function saveNewSpot() {
    const spotNumber = document.getElementById('newSpotNumber')?.value.trim().toUpperCase();
    const spotType   = document.getElementById('newSpotType')?.value || 'standard';
    const hourlyRate = parseFloat(document.getElementById('newSpotRate')?.value) || 5;
    const floor      = document.getElementById('newSpotFloor')?.value.trim() || 'Ground Floor';
    const msgEl      = document.getElementById('addSpotMsg');

    if (!spotNumber) {
        msgEl.style.cssText = 'display:block;background:#fee2e2;color:#dc2626;padding:10px;border-radius:8px;';
        msgEl.textContent = 'Please enter a spot number';
        return;
    }

    const slotId = `${PARKING_ID}_slot_${spotNumber}`;

    try {
        // Register slot in backend via IoT (creates it in memory + Firestore via patch)
        await apiFetch(
            `/api/v1/iot/slot-update?parking_id=${PARKING_ID}&slot_number=${spotNumber}&status=available&device_key=${DEVICE_KEY}`,
            { method: 'POST' }
        );

        // Save extra info to localStorage
        const saved = JSON.parse(localStorage.getItem('parkify_spot_edits') || '{}');
        saved[slotId] = { hourly_rate: hourlyRate, spot_type: spotType, status: 'available', floor };
        localStorage.setItem('parkify_spot_edits', JSON.stringify(saved));

        // Add to tracked IDs
        HTML_SLOT_IDS.add(slotId);

        // Add spot box to grid
        const grid = document.querySelector('.parking-grid');
        if (grid) {
            const box = document.createElement('div');
            box.className = 'spot-box free';
            box.dataset.id = slotId;
            box.dataset.status = 'Available';
            box.dataset.parkingId = PARKING_ID;
            box.innerHTML = `
                <div class="spot-id">${spotNumber}</div>
                <div class="spot-icon"><i class="fa-solid fa-car-side opacity-20"></i></div>
                <div class="spot-footer">Available</div>
                <div class="hover-overlay"><span>Click for details</span></div>`;
            grid.appendChild(box);
            initSpotModal();
        }

        msgEl.style.cssText = 'display:block;background:#d1fae5;color:#059669;padding:10px;border-radius:8px;';
        msgEl.textContent = `Spot ${spotNumber} added ✅`;

        await loadParkingSpots();
        setTimeout(() => closeAddSpotModal(), 1500);

    } catch(err) {
        msgEl.style.cssText = 'display:block;background:#fee2e2;color:#dc2626;padding:10px;border-radius:8px;';
        msgEl.textContent = err.message || 'Failed to add spot';
    }
}

// ── Quick Actions ─────────────────────────────────────────────
function navigateTo(section) {
    const link = document.querySelector(`[data-section="${section}"]`);
    if (link) link.click();
}

function generateReport() {
    const bookings = cacheGet(CACHE.bookings) || [];
    const slots    = cacheGet(CACHE.slots) || [];
    const today    = new Date().toLocaleDateString('en-US');

    const available  = slots.filter(s => s.status === 'available').length;
    const occupied   = slots.filter(s => s.status === 'occupied').length;
    const reserved   = slots.filter(s => s.status === 'reserved').length;
    const todayRev   = bookings
        .filter(b => b.created_at && new Date(b.created_at).toDateString() === new Date().toDateString())
        .reduce((s, b) => s + Number(b.amount || b.total_amount || 0), 0);

    const report = `PARKIFY DAILY REPORT — ${today}
=====================================
PARKING STATUS
  Total Spots:     ${slots.length}
  Available:       ${available}
  Occupied:        ${occupied}
  Reserved:        ${reserved}

REVENUE
  Today's Revenue: ${todayRev.toFixed(0)} EGP
  Total Bookings:  ${bookings.length}

Generated at: ${new Date().toLocaleTimeString()}
=====================================`;

    const blob = new Blob([report], { type: 'text/plain' });
    const a    = document.createElement('a');
    a.href     = URL.createObjectURL(blob);
    a.download = `parkify_report_${today.replace(/\//g,'-')}.txt`;
    a.click();
}