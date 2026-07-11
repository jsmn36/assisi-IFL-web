# 🏨 Guest Relationship Management (CRM) Module

The CRM module is a high-performance marketing and analytics engine integrated into the PMS Hotel Desktop. It centralizes guest stay history, preferences, and automated segmentation to power data-driven marketing campaigns.

---

## 📂 Directory Structure

```text
frontend/src/crm/
├── api/             # Unified API client (Switching between Mock & Real)
├── components/      # UI components (Shared and domain-specific)
│   ├── analytics/   # Recharts visualizations & KPI cards
│   ├── campaigns/   # Marketing campaign management & wizards
│   ├── guest/       # Profiles, stay history, and note-taking
│   ├── segments/    # Segment summaries and drill-down cards
│   └── shared/      # Reusable UI (Skeletons, ErrorCards, EmptyStates)
├── hooks/           # TanStack Query (React Query) implementations
├── mock/            # Detailed Phase 1 mock data (30+ guests)
├── pages/           # Main route-level entry points & layouts
├── store/           # Zustand global state (Filters, Modal states)
└── types/           # Strict TypeScript interfaces for the CRM domain
```

---

## ⚙️ Switching from Mock to Real API

The CRM follows a **Signature-Stable** architecture. The API client (`api/crmClient.ts`) uses the same functions for both local development and production.

- **Phase 1 (Mock)**: Default behavior. Functions return `mockDelay()` data.
- **Phase 2 (Production)**: Set `VITE_CRM_USE_MOCK=false` in your `.env` file. 

The application will automatically switch to calling the backend endpoints defined in the `CRM_BASE` constant within `crmClient.ts`.

---

## 🏷️ How to Add a New Segment Type

1.  **Define in Types**: Update `frontend/src/crm/types/crm.ts` and add your new segment to the `SegmentName` union type.
2.  **Add Metadata**: Update `SEGMENT_META` in `crm/types/crm.ts` to include a label, icon, and specific CSS color variables for your new segment.
3.  **Update Logic**: If using mock data, update the `deriveSegments()` function in `mockData.ts` to include the calculation logic for the new segment.

---

## 🛤️ How to Add a New Page/Route

1.  **Create the Page**: Add a new file in `frontend/src/crm/pages/`, e.g., `ReportsPage.tsx`.
2.  **Define the Route**: Open `frontend/src/App.tsx` (the main router) and add your new route as a child of the `CRMLayout` route.
3.  **Update Navigation**: In `frontend/src/crm/pages/CRMLayout.tsx`, add an entry to the `NAV_ITEMS` array. Specify the required permission if necessary (`can('view_reports')`).

---

## 🧠 How to Extend the Zustand Store

The global state is managed in `frontend/src/crm/store/crmStore.ts`.

1.  **Update Interface**: Add your new state property or setter function to the `CRMState` interface.
2.  **Add Initial State**: Define the default value inside the `create<CRMState>` function.
3.  **Implement Setter**: Write the implementation of your setter function using the `set()` method. 

*Example: Adding a toggle for a specific UI drawer.*

---

## 📡 How to Add a New API Endpoint

1.  **Define Interface**: Update `crm/types/crm.ts` with the expected request/response interface.
2.  **Update Client**: Add a new method to the appropriate object in `crm/api/crmClient.ts` (e.g., `crmGuestsApi` or a new `crmReportsApi`).
3.  **Implement Mock/Real Switch**:
    - Add a mock implementation that uses `mockDelay()`.
    - Add the real `http.get/post` implementation for Phase 2.
4.  **Create a Hook**: Add a matching `useQuery` or `useMutation` hook in the `crm/hooks/` directory.

---

## 💅 Styling & Best Practices

- **Components**: Use functional components with **Vanilla CSS-in-JS** (`React.CSSProperties`) for portability.
- **Animations**: Use the global `shimmer` keyframes (defined in `index.html`) for loading states.
- **Resilience**: Always wrap tables in an `overflowX: 'auto'` div and use the `ErrorCard` fallback for data fetching errors.
