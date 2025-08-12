import {readFileSync} from "fs"
import {defineConfig} from 'vitepress'

// Copied from https://github.com/equinor/vscode-lang-ert/blob/master/syntaxes/ert.tmLanguage.json
const ertLanguageGrammar = JSON.parse(readFileSync("./docs/ert.tmLanguage.json"))

// https://vitepress.dev/reference/site-config
export default defineConfig({
    title: "FMU sim2seis",
    description: "User documentation for using fmu-sim2seis",
    head: [
        ["link", {rel: "stylesheet", href: "https://unpkg.com/tailwindcss@^2/dist/tailwind.min.css"}]
    ],
    markdown: {
        math: true,
        languages: [ertLanguageGrammar]
    },
    themeConfig: {
        // https://vitepress.dev/reference/default-theme-config
        nav: [
            {text: 'Home', link: '/'},
        ],
        logo: {light: "/fmu_logo_light_mode.svg", dark: "/fmu_logo_dark_mode.svg"},
        sidebar: [
            {
                text: 'Introduction',
                items: [
                    {
                        text: 'Why sim2seis?', link: '/use-cases', items: [
                            {text: 'Petro-elastic model', link: '/static-and-dynamic-input'},
                            {text: 'Seismic Forward Modelling', link: '/seismic-forward'},
                            {text: 'Depth to Time Conversion', link: '/time-depth-conversion'},
                            {text: 'Relative seismic inversion', link: '/relative-seismic-inversion'},
                            {text: 'Attribute Maps', link: '/attribute-maps'},
                            {text: 'Observed Data Processing', link: '/observed-data'},
                            {text: 'Delete Intermediate Files', link: '/clean-up'},
                            {
                                text: 'QC of Results', link: '/qc', items: [
                                    {text: 'QC in RMS', link: '/qc_rms'},
                                    {text: 'QC in ResInsight', link: '/qc_resinsight'},
                                    {text: 'QC in Jupyter Notebooks', link: '/qc_jupyter_notebook'}
                                ]
                            },
                        ]
                    },
                ]
            },
            {
                text: 'Setup',
                items: [
                    {text: 'ERT configuration', link: '/ert-configuration'},
                    {text: 'Sim2seis configuration', link: '/sim2seis-configuration'},
                    {text: 'Input & output', link: '/input-output'}
                ]
            }
        ],

        socialLinks: [
            {icon: 'github', link: 'https://github.com/equinor/fmu-sim2seis'}
        ]
    }
})
