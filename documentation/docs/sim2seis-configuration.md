---
outline: deep
---

# SIM2SEIS configuration

Create, update or change a **fmu-sim2seis** configuration file. You can load an existing configuration file as starting point.
Default values are not filled in automatically; press **Populate defaults** to add them to the current form. Omitted
fields get their default values at run time.

<div ref="el" />

<script setup>
import { createElement } from 'react'
import { createRoot } from 'react-dom/client'
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { YamlEdit } from './yaml-edit/YamlEdit'

const el = ref()
let root
onMounted(() => {
  root = createRoot(el.value)
  root.render(createElement(YamlEdit, {}, null))
})
onBeforeUnmount(() => root?.unmount())
</script>
