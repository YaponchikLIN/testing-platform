const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('🔨 Начинаем сборку для NW.js...');

// Шаг 1: Сборка Vue приложения для NW.js
console.log('📦 Сборка Vue приложения для NW.js...');
try {
  // Устанавливаем переменную окружения для NW.js сборки
  process.env.BUILD_TARGET = 'nw';
  execSync('npm run build', { stdio: 'inherit', env: { ...process.env, BUILD_TARGET: 'nw' } });
  console.log('✅ Сборка Vue завершена успешно');
} catch (error) {
  console.error('❌ Ошибка при сборке Vue:', error.message);
  process.exit(1);
}

// Шаг 2: Поиск собранных файлов
const distPath = path.join(__dirname, 'dist');
const cssFiles = fs.readdirSync(path.join(distPath, 'css')).filter(f => f.endsWith('.css'));
const jsFiles = fs.readdirSync(path.join(distPath, 'js')).filter(f => f.endsWith('.js'));

console.log('📁 Найденные файлы:');
console.log('CSS:', cssFiles);
console.log('JS:', jsFiles);

// Шаг 3: Создание правильного index.html
const htmlContent = `<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width,initial-scale=1.0">
    <link rel="icon" href="favicon.ico">
    <title>Testing Platform</title>
${cssFiles.map(file => `    <link href="css/${file}" rel="stylesheet">`).join('\n')}
</head>
<body>
    <noscript>
        <strong>We're sorry but Testing Platform doesn't work properly without JavaScript enabled. Please enable it to continue.</strong>
    </noscript>
    <div id="app"></div>
${jsFiles.map(file => `    <script src="js/${file}"></script>`).join('\n')}
</body>
</html>`;

fs.writeFileSync(path.join(distPath, 'index.html'), htmlContent);
console.log('✅ index.html создан успешно');

console.log('🎉 Сборка для NW.js завершена! Теперь можно запустить: npm run nw-serve');