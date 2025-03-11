import { create } from 'zustand';
import api from '../config/api';
import type { DataDictionaryEntry } from '../types/api';

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
  updateEntry: (id: string, data: Partial<DataDictionaryEntry>) => Promise<void>;
  createEntry: (data: Omit<DataDictionaryEntry, 'id' | 'created_at' | 'updated_at'>) => Promise<void>;
  deleteEntry: (id: string) => Promise<void>;
  setSelectedEntry: (entry: DataDictionaryEntry | null) => void;
}

const useDictionaryStore = create<DictionaryState>((set, get) => ({
  entries: [],
  selectedEntry: null,
  isLoading: false,
  error: null,

  fetchEntries: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.get<DataDictionaryEntry[]>('/api/dictionary/entries');
      set({ entries: response.data, isLoading: false });
    } catch (error) {
      set({ error: 'Failed to fetch entries', isLoading: false });
      throw error;
    }
  },

  updateEntry: async (id: string, data: Partial<DataDictionaryEntry>) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.put<DataDictionaryEntry>(`/api/dictionary/entries/${id}`, data);
      const entries = get().entries.map((entry) =>
        entry.id === id ? response.data : entry
      );
      set({ entries, isLoading: false });
    } catch (error) {
      set({ error: 'Failed to update entry', isLoading: false });
      throw error;
    }
  },

  createEntry: async (data: Omit<DataDictionaryEntry, 'id' | 'created_at' | 'updated_at'>) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.post<DataDictionaryEntry>('/api/dictionary/entries', data);
      set((state) => ({
        entries: [...state.entries, response.data],
        isLoading: false,
      }));
    } catch (error) {
      set({ error: 'Failed to create entry', isLoading: false });
      throw error;
    }
  },

  deleteEntry: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      await api.delete(`/api/dictionary/entries/${id}`);
      set((state) => ({
        entries: state.entries.filter((entry) => entry.id !== id),
        isLoading: false,
      }));
    } catch (error) {
      set({ error: 'Failed to delete entry', isLoading: false });
      throw error;
    }
  },

  setSelectedEntry: (entry) => {
    set({ selectedEntry: entry });
  },
}));

export default useDictionaryStore; 