import { create } from 'zustand';

const useSelectionStore = create((set) => ({
  selection: {
    starters: [],
    subs: [],
    res: [],
    nis: []
  },
  setSelection: (newSelection) => set({ selection: newSelection }),


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
    movePlayer: (playerId, from, to) =>
  set((state) => {
    const newSelection = { ...state.selection };

    // Remove from current slot (preserve null if necessary)
    newSelection[from] = newSelection[from].map((p) =>
      p?.player_id === playerId ? null : p
    );

    // Avoid duplicates: clean from all groups
    for (const key of Object.keys(newSelection)) {
      newSelection[key] = newSelection[key].map((p) =>
        p?.player_id === playerId ? null : p
      );
    }

    // Insert into target group
    const player = state.selection[from].find((p) => p?.player_id === playerId);
    if (!player) return state;

    const insertIndex = newSelection[to].findIndex((p) => !p);
    if (insertIndex !== -1) {
      newSelection[to][insertIndex] = player;
    } else {
      newSelection[to].push(player); // for dynamic groups like nis
    }

    return { selection: newSelection };
  })

}));
export default useSelectionStore;
