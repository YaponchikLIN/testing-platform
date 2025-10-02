<template>
  <div class="app-container">
    <div class="main-wrapper">
      <Card class="main-card">
        <template #title></template>
        <template #content>
          <div class="content-grid">
            <div class="formgrid grid">
              <Workflow />
            </div>
          </div>
        </template>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from "vue";
import { useConfigStore } from "./stores/config.store";
import Workflow from "./blocks/Workflow.vue";

const configStore = useConfigStore();
</script>

<style>
/* Основной контейнер приложения */
.app-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 2rem 1rem;
}

/* Центральный wrapper с максимальной шириной */
.main-wrapper {
  width: 100%;
  max-width: 1400px;
}

/* Основная карточка */
.main-card {
  width: 100%;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  overflow: hidden;
}

/* Контент грид */
.content-grid {
  width: 100%;
}

/* Mobile-first адаптивные breakpoints */
@media (max-width: 320px) {
  .app-container {
    padding: 0.5rem 0.25rem;
  }
}

@media (max-width: 576px) {
  .app-container {
    padding: 1rem 0.5rem;
  }

  .main-wrapper {
    max-width: 100%;
  }
}

@media (max-width: 768px) {
  .app-container {
    padding: 1.5rem 0.75rem;
  }

  .main-wrapper {
    max-width: 100%;
  }
}

@media (max-width: 992px) {
  .main-wrapper {
    max-width: 900px;
  }

  .app-container {
    padding: 2rem 1rem;
  }
}

@media (max-width: 1200px) {
  .main-wrapper {
    max-width: 1100px;
  }
}

@media (min-width: 1400px) {
  .main-wrapper {
    max-width: 1600px;
  }

  .app-container {
    padding: 3rem 2rem;
  }
}

.field.col {
  padding-bottom: 10px;
  padding-left: 5px;
  padding-right: 5px;
  flex: 1 0 50%;
}

.data {
  overflow: hidden;
}

span {
  overflow: hidden;
  text-overflow: ellipsis;
}

h5 {
  margin-top: 3px;
}

@media screen and (min-width: 1000px) {
  h5 {
    font-size: 1.25rem;
  }
}

.card {
  overflow: hidden;
  min-width: 200px;
}

.formgrid.grid {
  /* display: flex; */
  flex-wrap: nowrap;
  width: 100%;
  min-width: 0;
}

.field.col {
  min-width: 0;
  overflow: hidden;
}

.p-span-title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.data {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

.image-icon {
  width: 24px;
  height: 24px;
  margin-right: -5px;
  margin-top: -3px;
}
</style>
