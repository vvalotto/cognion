import '@testing-library/jest-dom/vitest'
import { configure } from '@testing-library/react'

// Espera máxima de findBy*/waitFor (US-ADJ-55). El default de 1 s se agota bajo la carga que genera la
// propia suite completa aunque el test espere bien el dato: medido, p99 ~1,9 s y máximo ~4 s. Solo cambia
// algo si el dato nunca llega (el test falla a los 5 s en vez de a 1 s).
configure({ asyncUtilTimeout: 5000 })
