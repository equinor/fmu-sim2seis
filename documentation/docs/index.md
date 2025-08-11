---
# https://vitepress.dev/reference/default-theme-home-page
layout: home

hero:
  name: Sim2seis modelling
  text: "User documentation"
  tagline: Calculate synthetic seismic from simulation results
  actions:
    - theme: brand
      text: Why and how sim2seis?
      link: ./use-cases
    - theme: brand
      text: ERT configuration
      link: ./ert-configuration
    - theme: brand
      text: Sim2seis configuration
      link: ./sim2seis-configuration
    - theme: alt
      text: Input & output overview
      link: ./input-output

features:
  - icon: 🛠️
    title: Less maintenance
    details: No need for custom scripts in your FMU or RMS project. Sim2seis is maintained centrally by Equinor, and available as pre-installert ERT forward models.
  - icon: 🤝
    title: Shared rock physics library
    details: FMU sim2seis uses the same underlying rock physics library as RokDoc plugins - ensuring consistent output across the software portfolio.
---
