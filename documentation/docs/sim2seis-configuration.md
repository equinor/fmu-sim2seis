---
outline: deep
---

# SIM2SEIS configuration


Create, update or change a **fmu-sim2seis** configuration file. You can load an existing configuration file as starting point.

<div ref="el" />

<script setup>
import { createElement } from 'react'
import { createRoot } from 'react-dom/client'
import { ref, onMounted } from 'vue'
import { YamlEdit } from './yaml-edit/YamlEdit'

const el = ref()
onMounted(() => {
  const root = createRoot(el.value)
  root.render(createElement(YamlEdit, {}, null))
})
</script>

<style>
 input.form-control, select.form-control {
    background-color: rgb(245 245 245);
    border-radius: 5px;
    padding: 3px;
    border: 1px solid;
    border-color: #ccc;
    box-shadow: 0 1+px 25px -5px rgb(0 0 0 / 0.05);
}

input.form-control {
    min-width: 400px;
}

select.form-control:hover {
  cursor: pointer;
}

.dark input.form-control {
  background-color: rgb(50 50 50);
  border-color: #666;
}

.form-group {
  margin-top: 20px;
  margin-left: 15px;
  padding-top: 5px;
  padding-bottom: 5px;
}

.control-label {
  font-weight: 500;
}

.field-description {
  font-size: small;
}

legend {
  font-size: 20px;
  font-weight: 700;
}

.btn-group {
  max-width: 300px;
  margin: auto;
  margin-bottom: 20px;
}

.glyphicon {
  position: relative;
  top: 1px;
  display: inline-block;
  font-family: "Glyphicons Halflings";
  font-style: normal;
  font-weight: normal;
  line-height: 1;
}

.glyphicon-plus:before {
  content: "➕";
  padding: 5px;
  border-radius: 5px;
  background-color: oklch(92.5% 0.084 155.995)
}

.dark .glyphicon-plus:before {
  background-color: oklch(39.3% 0.095 152.535)
}

.glyphicon-remove:before {
  content: "🗑️";
  padding: 5px;
  border-radius: 5px;
  background-color: oklch(93.6% 0.032 17.717);
  border: 1px solid oklch(88.5% 0.062 18.334);
}
.glyphicon-arrow-up:before {
  content: "🢁";
}
.glyphicon-arrow-down:before {
  content: "🢃";
}

.checkbox > label {
  display: flex;
  gap: 10px;
  font-weight: 500;
}

input[type='text']:read-only{
  background: lightgrey;
  cursor: not-allowed;
}

.text-danger {
    color: oklch(57.7% 0.245 27.325);
    background-color: oklch(93.6% 0.032 17.717);
    padding: 2px;
    padding-left: 6px;
    padding-right: 6px;
    border-radius: 5px;
    width: fit-content;
}

li.text-danger::marker {
  content: "⚠";
}

</style>
