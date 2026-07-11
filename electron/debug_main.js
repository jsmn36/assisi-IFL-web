const electron = require('electron');
console.log('[DEBUG] typeof electron:', typeof electron);
console.log('[DEBUG] electron value:', electron);
if (typeof electron === 'string') {
  console.log('[DEBUG] electron is a string (node_modules/electron, not built-in)!');
} else {
  const { app } = electron;
  console.log('[DEBUG] app:', app);
}
