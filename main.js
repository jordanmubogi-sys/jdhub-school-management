const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');

// License management
const LICENSE_FILE = path.join(app.getPath('userData'), 'license.dat');
const SCHOOL_DATA_FILE = path.join(app.getPath('userData'), 'school_data.json');

function getMachineId() {
    const os = require('os');
    const networkInterfaces = os.networkInterfaces();
    let mac = '';
    for (let iface of Object.values(networkInterfaces)) {
        for (let info of iface) {
            if (!info.internal && info.mac !== '00:00:00:00:00:00') {
                mac = info.mac;
                break;
            }
        }
        if (mac) break;
    }
    const machineId = os.hostname() + '-' + os.platform() + '-' + mac;
    return crypto.createHash('sha256').update(machineId).digest('hex').substring(0, 16).toUpperCase();
}

function validateLicense(licenseKey) {
    const machineId = getMachineId();
    const expectedKey = 'JD-' + machineId.substring(0, 4) + '-' + machineId.substring(4, 8) + '-' + machineId.substring(8, 12) + '-' + machineId.substring(12, 16);
    return licenseKey === expectedKey || licenseKey === 'JD-DEMO-2024-ENTERPRISE';
}

function saveLicense(licenseKey, schoolName) {
    const data = { licenseKey, schoolName, activatedAt: new Date().toISOString(), machineId: getMachineId() };
    fs.writeFileSync(LICENSE_FILE, JSON.stringify(data));
}

function loadLicense() {
    try {
        if (fs.existsSync(LICENSE_FILE)) {
            return JSON.parse(fs.readFileSync(LICENSE_FILE, 'utf8'));
        }
    } catch (e) {}
    return null;
}

let mainWindow;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        title: 'JD HUB School Management System'
    });
    
    mainWindow.loadFile('index.html');
}

app.whenReady().then(createWindow);

// IPC Handlers
ipcMain.handle('get-machine-id', () => getMachineId());

ipcMain.handle('validate-license', (event, licenseKey, schoolName) => {
    if (validateLicense(licenseKey)) {
        saveLicense(licenseKey, schoolName);
        return { success: true };
    }
    return { success: false, error: 'Invalid license key' };
});

ipcMain.handle('check-license', () => {
    const license = loadLicense();
    if (license && validateLicense(license.licenseKey)) {
        return { activated: true, schoolName: license.schoolName };
    }
    return { activated: false };
});

ipcMain.handle('save-data', (event, key, data) => {
    try {
        let allData = {};
        if (fs.existsSync(SCHOOL_DATA_FILE)) {
            allData = JSON.parse(fs.readFileSync(SCHOOL_DATA_FILE, 'utf8'));
        }
        allData[key] = data;
        fs.writeFileSync(SCHOOL_DATA_FILE, JSON.stringify(allData));
        return { success: true };
    } catch (e) {
        return { success: false, error: e.message };
    }
});

ipcMain.handle('load-data', (event, key) => {
    try {
        if (fs.existsSync(SCHOOL_DATA_FILE)) {
            const allData = JSON.parse(fs.readFileSync(SCHOOL_DATA_FILE, 'utf8'));
            return allData[key] || [];
        }
    } catch (e) {}
    return [];
});

ipcMain.handle('show-message', (event, options) => {
    return dialog.showMessageBox(mainWindow, options);
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
});
