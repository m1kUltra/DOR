import { create } from 'zustand';

const useSelectionStore = create((set) => ({
  selection: {
    starters: [],
    subs: [],
    res: [],
    nis: []
  },
  setSelection: (newSelection) => set({ selection: newSelection }),

  movePlayer: (playerId, from, to) =>
    set((state) => {
      const player = state.selection[from].find((p) => p.player_id === playerId);
      if (!player) return state;
      return {
        selection: {
          ...state.selection,
          [from]: state.selection[from].filter((p) => p.player_id !== playerId),
          [to]: [...state.selection[to], player],
        },
      };
    }),

  updatePosition: (playerId, newPos) =>
    set((state) => {
      for (const key of Object.keys(state.selection)) {
        const idx = state.selection[key].findIndex((p) => p.player_id === playerId);
        if (idx !== -1) {
          const updated = [...state.selection[key]];
          updated[idx] = { ...updated[idx], position: newPos };
          return { selection: { ...state.selection, [key]: updated } };
        }
      }
      return state;
    }),
}));
export default useSelectionStore;
