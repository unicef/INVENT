import path from 'path'
import dotenv from 'dotenv'

// Load default .env file
const result = dotenv.config()

if (result.error) {
  console.log('\x1B[31m%s\x1B[0m', 'Missing .env file, follow the README instructions')
  throw result.error
}

console.log('Enable Vue dev tools:', process.env.VUE_DEVTOOLS === 'true')

const features = ['default', 'fetch', 'Object.entries', 'Object.from', 'IntersectionObserver', 'EventSource'].join(
  '%2C'
)

const loginUrl =
  'https://login.microsoftonline.com/' +
  (process.env.AZURE_TENANT || '') +
  '/oauth2/v2.0/authorize?client_id=' +
  (process.env.AZURE_CLIENT_ID || '') +
  '&response_type=code&redirect_uri=' +
  (process.env.AZURE_REDIRECT_URI || 'http://localhost/accounts/azure/login/callback/') +
  '&response_mode=fragment&scope=openid offline_access'

const config = {
  vue: {
    config: {
      devtools: process.env.VUE_DEVTOOLS === 'true', // Enable devtools if VUE_DEVTOOLS is true
    },
  },
  head: {
    title: "Invent: UNICEF's T4D and Innovation Inventory",
    meta: [
      { charset: 'utf-8' },
      { name: 'viewport', content: 'width=device-width, initial-scale=1' },
      {
        hid: 'description',
        name: 'description',
        content: "Invent: UNICEF's T4D and Innovation Inventory",
      },
    ],
    link: [
      { rel: 'icon', type: 'image/ico', href: '/favicon.ico' },
      // {
      //   rel: "stylesheet",
      //   href:
      //     "https://fonts.googleapis.com/css?family=Roboto:400,400i,700,700i&display=swap"
      // },
      // {
      //   rel: "stylesheet",
      //   href:
      //     "https://fonts.googleapis.com/css?family=Roboto:300,400,500,700|Material+Icons"
      // }
    ],
    script: [
      {
        src: `https://polyfill.io/v3/polyfill.min.js?features=${features}`,
        body: true,
      },
    ],
  },
  css: ['~assets/style/main.sass', '~assets/style/main.less'],
  env: {
    loginUrl,
    SENTRY_DSN: process.env.SENTRY_DSN,
    NUXT_ENV: process.env.NUXT_ENV,
    SENTRY_ENVIRONMENT: process.env.SENTRY_ENVIRONMENT,
  },
  plugins: [
    { src: '~plugins/eventfix.js', ssr: false },
    { src: '~plugins/extends.js', ssr: false },
    { src: '~plugins/axios.js', ssr: true },
    { src: '~plugins/vee-validate.js', ssr: true },
    { src: '~plugins/vue-leaflet.js', ssr: false },
    { src: '~plugins/element.js', ssr: true },
    { src: '~plugins/i18n.js', ssr: true },
    { src: '~plugins/watchHead.js', ssr: false },
    { src: '~plugins/directives.js', ssr: false },
    { src: '~plugins/charts.js', ssr: false },
    // { src: '~plugins/no-unicef-record.js', ssr: false },
    { src: '~plugins/filters.js' },
  ],
  modules: [
    '@nuxtjs/axios',
    '@nuxtjs/proxy',
    'nuxt-fontawesome',
    '@nuxtjs/sentry',
    [
      'nuxt-matomo',
      {
        matomoUrl: process.env.MATOMO_URL,
        siteId: process.env.MATOMO_SITEID,
        debug: process.env.MATOMO_DEBUG,
      },
    ],
    // 'nuxt-purgecss',
    [
      'nuxt-i18n',
      {
        locales: [
          {
            code: 'en',
            iso: 'en-GB',
            name: 'English',
            file: 'en-GB.js',
          },
          {
            code: 'fr',
            iso: 'fr-FR',
            name: 'Français',
            file: 'fr-FR.js',
          },
          {
            code: 'es',
            iso: 'es-ES',
            name: 'Español',
            file: 'es-ES.js',
          },
          {
            code: 'pt',
            iso: 'pt-PT',
            name: 'Português',
            file: 'pt-PT.js',
          },
          {
            code: 'ar',
            iso: 'ar-AR',
            name: 'Arabic',
            file: 'ar-AR.js',
          },
        ],
        lazy: true,
        langDir: 'lang/',
        strategy: 'prefix',
        rootRedirect: 'en/-/',
        defaultLocale: 'en',
        seo: false,
        vueI18n: {
          fallbackLocale: 'en',
          silentTranslationWarn: true,
        },
        vuex: {
          moduleName: 'i18n',
          mutations: {
            setLocale: 'I18N_SET_LOCALE',
            setMessages: false,
          },
        },
        detectBrowserLanguage: {
          useCookie: true,
          cookieKey: 'i18n_redirected',
        },
      },
    ],
  ],

  sentry: {
    dsn: process.env.SENTRY_DSN || '',
    tracing: true,
    logLevel: process.env.NODE_ENV === 'production' ? 'error' : 'debug',
    config: {
      environment: process.env.SENTRY_ENVIRONMENT || 'unknown',
    },
    disabled: process.env.NODE_ENV !== 'production', // should disable when running locally even if sentry DSN is set
    clientIntegrations: {
      Vue: { tracing: true },
    },
  },
  fontawesome: {
    component: 'fa',
    imports: [
      {
        set: '@fortawesome/free-solid-svg-icons',
        icons: ['fas'],
      },
      {
        set: '@fortawesome/free-regular-svg-icons',
        icons: ['far'],
      },
    ],
  },
  proxy: {},
  axios: {
    baseURL: 'http://localhost:80/',
    browserBaseURL: '/',
    credentials: true,
    retry: false,
  },
  router: {
    // middleware: ['auth', 'noUnicefRecords', 'reset', 'tracking'],
    middleware: ['auth', 'reset', 'tracking'],
    base: '/',
  },
  // purgeCSS: {
  //   whitelistPatterns: () => [/\b[^\s]*(nuxt|leaflet|vue2-leaflet|el)[^\s]*\b/]
  // },
  loading: '~/components/DhaLoader.vue',
  render: {
    resourceHints: false,
  },
  build: {
    babel: {
      presets({ isServer }) {
        const targets = isServer ? { node: '14' } : { ie: '11' }
        return [[require.resolve('@nuxt/babel-preset-app'), { targets }]]
      },
    },
    extractCSS: true,
    optimization: {},
    // transpile: ['redux', 'redux-async-thunk'],
    extend(config, { isDev }) {
      config.plugins.forEach(function (plugin) {
        if (plugin.constructor && plugin.constructor.name === 'ExtractCssChunksPlugin') {
          plugin.options.ignoreOrder = true
        }
      })
      config.module.rules.push({
        test: /\.html$/,
        loader: 'html-loader',
        exclude: /(node_modules)/,
      })
      if (isDev && process.client) {
        config.module.rules.push({
          enforce: 'pre',
          test: /\.(js|vue)$/,
          loader: 'eslint-loader',
          exclude: /(node_modules)/,
        })
      }
      config.resolve.alias.leaflet = path.join(__dirname, 'node_modules/leaflet')
      // config.plugins.push(new bundlebuddy());
    },
  },
}

if (process.env.NODE_ENV !== 'production') {
  config.axios = {
    proxy: true,
    credentials: true,
  }
  config.proxy = {
    '/api/': { target: 'http://localhost/', secure: false },
    '/media/': { target: 'http://localhost/', secure: false },
    '/static/': { target: 'http://localhost/', secure: false },
    '/translation/': { target: 'http://localhost/', secure: false },
  }
}
export default config
