const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  lintOnSave: false,
  transpileDependencies: true,
  publicPath: './', // Относительные пути для Electron
  
  configureWebpack: {
    devtool: 'source-map'
  },
  
  devServer: {
    port: 8081
  },
  
  css: {
    loaderOptions: {
      scss: {
        // Стили удалены
      }
    }
  }
})
