---
outline: deep
---

# Interval definition

Create, update or check an interval definition file for [attribute maps](./attribute-maps.md). You can load an
existing file as starting point. Cube- and window-level observation error blocks are only included when their
checkbox is ticked. Per-attribute adjustments are added to a window by ticking **Add per-attribute overrides**
and pressing **Add attribute override**, using the attribute name (e.g. `rms`) as key; the attribute must also be listed under
`global.attributes`. Default values are not filled in automatically; press **Populate defaults** to add them to the
current form, including cubes and windows added so far. Omitted fields get their default values at run time.

<div ref="el" />

<script setup>
import { createElement } from 'react'
import { createRoot } from 'react-dom/client'
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { YamlEdit } from './yaml-edit/YamlEdit'
import { intervalSchema } from './yaml-edit/schema'
import { intervalUiSchema, validateIntervalConfig } from './yaml-edit/rjsf-extras'

const el = ref()
let root
onMounted(() => {
  root = createRoot(el.value)
  root.render(createElement(YamlEdit, { schema: intervalSchema, uiSchema: intervalUiSchema, customValidate: validateIntervalConfig, storageKey: 'intervalFormData' }, null))
})
onBeforeUnmount(() => root?.unmount())
</script>
