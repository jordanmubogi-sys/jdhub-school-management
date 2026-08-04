const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    getMachineId: () => ipcRenderer.invoke('get-machine-id'),
    validateLicense: (key, school) => ipcRenderer.invoke('validate-license', key, school),
    checkLicense: () => ipcRenderer.invoke('check-license'),
    saveData: (key, data) => ipcRenderer.invoke('save-data', key, data),
    loadData: (key) => ipcRenderer.invoke('load-data', key),
    showMessage: (options) => ipcRenderer.invoke('show-message', options)
});
