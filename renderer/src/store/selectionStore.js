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


   movePlayer: (playerId, fromGroup, toGroup, targetIndex) =>
  set((state) => {
    const newSelection = { ...state.selection };

    // find source
    const fromIndex = newSelection[fromGroup].findIndex((p) => p?.player_id === playerId);
    if (fromIndex === -1) return state;

    const sourcePlayer = newSelection[fromGroup][fromIndex];
    const targetPlayer = newSelection[toGroup][targetIndex];

    // if same group -> swap
    if (fromGroup === toGroup) {
      const updated = [...newSelection[fromGroup]];
      // perform swap
      updated[fromIndex] = targetPlayer;
      updated[targetIndex] = sourcePlayer;
      newSelection[fromGroup] = updated;
      return { selection: newSelection };
    }

    // different groups -> also swap (target may be empty)
    const updatedFrom = [...newSelection[fromGroup]];
    const updatedTo = [...newSelection[toGroup]];

    updatedFrom[fromIndex] = targetPlayer || null; // may be null if empty slot
    updatedTo[targetIndex] = sourcePlayer;

    newSelection[fromGroup] = updatedFrom;
    newSelection[toGroup] = updatedTo;

    return { selection: newSelection };
  }),


}));
export default useSelectionStore;
