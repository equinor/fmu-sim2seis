import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "FMU sim2seis",
  description: "User documentation for using fmu-sim2seis",
  head: [
    ["link", { rel: "stylesheet", href: "https://unpkg.com/tailwindcss@^2/dist/tailwind.min.css"}]
  ],
  markdown: {
    math: true
  },
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: 'Home', link: '/' },
    ],
    logo: { light: "/fmu_logo_light_mode.svg", dark: "/fmu_logo_dark_mode.svg"},
    sidebar: [
      { text: 'Introduction',
        items: [
          { text: 'Why sim2seis?', link: '/use-cases' },
        ]},
      {
        text: 'Setup',
        items: [
          { text: 'ERT configuration', link: '/ert-configuration' },
          { text: 'Sim2seis configuration', link: '/sim2seis-configuration' },
          { text: 'Input & output', link: '/input-output' }
        ]
      }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/equinor/fmu-sim2seis' }
    ]
  }
})
