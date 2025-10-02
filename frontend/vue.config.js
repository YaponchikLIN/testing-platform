const { defineConfig } = require('@vue/cli-service')
const path = require('path')

module.exports = defineConfig({
  lintOnSave: false,
  transpileDependencies: true,
  
  configureWebpack: {
    devtool: 'source-map',
    entry: {
      app: './src/main.js'
    },
    output: {
      filename: 'js/[name].[contenthash:8].js',
      chunkFilename: 'js/[name].[contenthash:8].js'
    }
  },
  
  chainWebpack: config => {
    if (process.env.NODE_ENV === 'production') {
      // В production отключаем HTML плагины для NW.js
      config.plugins.delete('html')
      config.plugins.delete('preload')
      config.plugins.delete('prefetch')
      
      // Настраиваем copy plugin, исключая index.html
      config.plugins.delete('copy')
      const CopyWebpackPlugin = require('copy-webpack-plugin')
      config.plugin('copy').use(CopyWebpackPlugin, [{
        patterns: [{
          from: path.resolve(__dirname, 'public'),
          to: path.resolve(__dirname, 'dist'),
          globOptions: {
            ignore: ['**/index.html', '**/index-dev.html']
          }
        }]
      }])
    } else {
      // В режиме разработки используем отдельный шаблон
      config.plugin('html').tap(args => {
        args[0].template = path.resolve(__dirname, 'public/index-dev.html')
        return args
      })
      
      // Исключаем index.html из копирования в режиме разработки
      config.plugin('copy').tap(args => {
        args[0].patterns[0].globOptions = {
          ignore: ['**/index.html', '**/index-dev.html']
        }
        return args
      })
    }
  },
  
  devServer: {
    static: {
      directory: path.join(__dirname, 'public')
    },
    historyApiFallback: {
      index: '/index.html'
    }
  },
  
  css: {
    loaderOptions: {
      scss: {
        // Стили удалены
      }
    }
  }
})
