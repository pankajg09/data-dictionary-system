import { create } from 'zustand';
import api from '../config/api';
import { DataDictionaryEntry } from '../types/api';

export interface DictionaryEntry {
  id: number;
  table_name: string;
  column_name: string;
  data_type: string;
  description: string;
  valid_values: any;
  relationships: any;
  source: string;
  version: string;
  created_at: string;
  updated_at: string;
}

interface DictionaryState {
  entries: DataDictionaryEntry[];
  selectedEntry: DataDictionaryEntry | null;
  isLoading: boolean;
  error: string | null;
  fetchEntries: () => Promise<void>;
  updateEntry: (id: number, data: Partial<DataDictionaryEntry>) => Promise<void>;
  createEntry: (data: Omit<DataDictionaryEntry, 'id'>) => Promise<void>;
  deleteEntry: (id: number) => Promise<void>;
  setSelectedEntry: (entry: DataDictionaryEntry | null) => void;
}

const useDictionaryStore = create<DictionaryState>((set, get) => ({
  entries: [],
  selectedEntry: null,
  isLoading: false,
  error: null,

  fetchEntries: async () => {
    try {
      set({ isLoading: true, error: null });
      const response = await api.get<DataDictionaryEntry[]>('/api/dictionary');
      set({ entries: response.data, isLoading: false });
    } catch (error) {
      set({ error: 'Failed to fetch entries', isLoading: false });
      console.error('Error fetching entries:', error);
    }
  },

  updateEntry: async (id: number, data: Partial<DataDictionaryEntry>) => {
    try {
      set({ isLoading: true, error: null });
      const response = await api.put<DataDictionaryEntry>(`/api/dictionary/entries/${id}`, data);
      const entries = get().entries.map((entry) =>
        entry.id === id ? response.data : entry
      );
      set({ entries, isLoading: false });
    } catch (error) {
      set({ error: 'Failed to update entry', isLoading: false });
      console.error('Error updating entry:', error);
    }
  },

  createEntry: async (data: Omit<DataDictionaryEntry, 'id'>) => {
    try {
      set({ isLoading: true, error: null });
      const response = await api.post<DataDictionaryEntry>('/api/dictionary/entries', data);
      set((state) => ({
        entries: [...state.entries, response.data],
        isLoading: false,
      }));
    } catch (error) {
      set({ error: 'Failed to create entry', isLoading: false });
      console.error('Error creating entry:', error);
    }
  },

  deleteEntry: async (id: number) => {
    try {
      set({ isLoading: true, error: null });
      await api.delete(`/api/dictionary/entries/${id}`);
      set((state) => ({
        entries: state.entries.filter((entry) => entry.id !== id),
        isLoading: false,
      }));
    } catch (error) {
      set({ error: 'Failed to delete entry', isLoading: false });
      console.error('Error deleting entry:', error);
    }
  },

  setSelectedEntry: (entry) => {
    set({ selectedEntry: entry });
  },
}));

export default useDictionaryStore; 