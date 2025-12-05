<template>
  <div class="flex flex-col h-screen p-2">
    <select class="border border-gray-400" v-model="type">
      <option value="composition">Composition API</option>
      <option value="legacy">Legacy</option>
    </select>
    <component :is="component"></component>
  </div>
</template>

<script>
import { ref, computed } from 'vue';
import VueComposition from './vue-composition';
import VueLegacy from './vue-legacy';

export default {
  components: {
    VueComposition,
    VueLegacy,
  },
  setup() {
    const type = ref('composition');
    const component = computed(
      () =>
        ({
          composition: VueComposition,
          legacy: VueLegacy,
        }[type.value])
    );
    return {
      type,
      component,
    };
  },
};
</script>

<style>
@import url('https://cdn.jsdelivr.net/npm/tailwindcss@2.2.0/dist/tailwind.min.css');

h1,
p {
  font-family: Lato;
}
</style>
