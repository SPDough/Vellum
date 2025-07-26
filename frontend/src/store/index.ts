import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { User, Workspace, NavigationItem, Page, SOPDocument, Trade } from '@/types';

// Auth Store
interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  token: string | null;
  login: (user: User, token: string) => void;
  logout: () => void;
  updateUser: (user: Partial<User>) => void;
  checkAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  devtools(
    (set) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      token: null,
      login: (user, token) =>
        set({
          user,
          token,
          isAuthenticated: true,
          isLoading: false,
        }),
      logout: () =>
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          isLoading: false,
        }),
      updateUser: (userData) =>
        set((state) => ({
          user: state.user ? { ...state.user, ...userData } : null,
        })),
      checkAuth: () => {
        const token = localStorage.getItem('auth_token');
        if (token) {
          // In a real app, you'd validate the token with the server
          set({ isAuthenticated: true, token });
        } else {
          set({ isAuthenticated: false, token: null, user: null });
        }
      },
    }),
    {
      name: 'auth-store',
    }
  )
);

// Workspace Store (Notion-style)
interface WorkspaceState {
  currentWorkspace: Workspace | null;
  workspaces: Workspace[];
  currentPage: Page | null;
  navigation: NavigationItem[];
  sidebarCollapsed: boolean;
  breadcrumbs: NavigationItem[];
  
  // Actions
  setCurrentWorkspace: (workspace: Workspace) => void;
  setCurrentPage: (page: Page) => void;
  addPage: (page: Page) => void;
  updatePage: (pageId: string, updates: Partial<Page>) => void;
  deletePage: (pageId: string) => void;
  toggleSidebar: () => void;
  setBreadcrumbs: (breadcrumbs: NavigationItem[]) => void;
  updateNavigation: (navigation: NavigationItem[]) => void;
}

export const useWorkspaceStore = create<WorkspaceState>()(
  devtools(
    (set, _get) => ({
      currentWorkspace: null,
      workspaces: [],
      currentPage: null,
      navigation: [],
      sidebarCollapsed: false,
      breadcrumbs: [],
      
      setCurrentWorkspace: (workspace) =>
        set({
          currentWorkspace: workspace,
          navigation: workspace.pages,
        }),
      
      setCurrentPage: (page) =>
        set({ currentPage: page }),
      
      addPage: (page) =>
        set((state) => {
          const updatedNavigation = [...state.navigation];
          const newNavItem: NavigationItem = {
            id: page.id,
            title: page.title,
            icon: page.icon || 'description',
            path: `/page/${page.id}`,
            type: 'page',
            parent_id: page.parent_id,
          };
          
          if (page.parent_id) {
            // Add as child to parent
            const addToParent = (items: NavigationItem[]): NavigationItem[] =>
              items.map((item) => {
                if (item.id === page.parent_id) {
                  return {
                    ...item,
                    children: [...(item.children || []), newNavItem],
                  };
                }
                if (item.children) {
                  return {
                    ...item,
                    children: addToParent(item.children),
                  };
                }
                return item;
              });
            
            return { navigation: addToParent(updatedNavigation) };
          } else {
            // Add as top-level page
            updatedNavigation.push(newNavItem);
            return { navigation: updatedNavigation };
          }
        }),
      
      updatePage: (pageId, updates) =>
        set((state) => ({
          currentPage:
            state.currentPage?.id === pageId
              ? { ...state.currentPage, ...updates }
              : state.currentPage,
        })),
      
      deletePage: (pageId) =>
        set((state) => {
          const removeFromNavigation = (items: NavigationItem[]): NavigationItem[] =>
            items
              .filter((item) => item.id !== pageId)
              .map((item) => ({
                ...item,
                children: item.children ? removeFromNavigation(item.children) : undefined,
              }));
          
          return {
            navigation: removeFromNavigation(state.navigation),
            currentPage: state.currentPage?.id === pageId ? null : state.currentPage,
          };
        }),
      
      toggleSidebar: () =>
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      
      setBreadcrumbs: (breadcrumbs) =>
        set({ breadcrumbs }),
      
      updateNavigation: (navigation) =>
        set({ navigation }),
    }),
    {
      name: 'workspace-store',
    }
  )
);

// Data Store (for SOP documents, trades, etc.)
interface DataState {
  sopDocuments: SOPDocument[];
  trades: Trade[];
  selectedSOP: SOPDocument | null;
  selectedTrade: Trade | null;
  loading: boolean;
  error: string | null;
  
  // Actions
  setSopDocuments: (documents: SOPDocument[]) => void;
  addSopDocument: (document: SOPDocument) => void;
  updateSopDocument: (id: string, updates: Partial<SOPDocument>) => void;
  setSelectedSOP: (document: SOPDocument | null) => void;
  
  setTrades: (trades: Trade[]) => void;
  addTrade: (trade: Trade) => void;
  updateTrade: (id: string, updates: Partial<Trade>) => void;
  setSelectedTrade: (trade: Trade | null) => void;
  
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useDataStore = create<DataState>()(
  devtools(
    (set) => ({
      sopDocuments: [],
      trades: [],
      selectedSOP: null,
      selectedTrade: null,
      loading: false,
      error: null,
      
      setSopDocuments: (documents) => set({ sopDocuments: documents }),
      addSopDocument: (document) =>
        set((state) => ({
          sopDocuments: [...state.sopDocuments, document],
        })),
      updateSopDocument: (id, updates) =>
        set((state) => ({
          sopDocuments: state.sopDocuments.map((doc) =>
            doc.id === id ? { ...doc, ...updates } : doc
          ),
          selectedSOP:
            state.selectedSOP?.id === id
              ? { ...state.selectedSOP, ...updates }
              : state.selectedSOP,
        })),
      setSelectedSOP: (document) => set({ selectedSOP: document }),
      
      setTrades: (trades) => set({ trades }),
      addTrade: (trade) =>
        set((state) => ({
          trades: [...state.trades, trade],
        })),
      updateTrade: (id, updates) =>
        set((state) => ({
          trades: state.trades.map((trade) =>
            trade.id === id ? { ...trade, ...updates } : trade
          ),
          selectedTrade:
            state.selectedTrade?.id === id
              ? { ...state.selectedTrade, ...updates }
              : state.selectedTrade,
        })),
      setSelectedTrade: (trade) => set({ selectedTrade: trade }),
      
      setLoading: (loading) => set({ loading }),
      setError: (error) => set({ error }),
    }),
    {
      name: 'data-store',
    }
  )
);

// UI Store
interface UIState {
  theme: 'light' | 'dark';
  searchOpen: boolean;
  searchQuery: string;
  commandPaletteOpen: boolean;
  selectedBlocks: string[];
  
  // Actions
  setTheme: (theme: 'light' | 'dark') => void;
  toggleSearch: () => void;
  setSearchQuery: (query: string) => void;
  toggleCommandPalette: () => void;
  setSelectedBlocks: (blocks: string[]) => void;
  clearSelection: () => void;
}

export const useUIStore = create<UIState>()(
  devtools(
    (set) => ({
      theme: 'light',
      searchOpen: false,
      searchQuery: '',
      commandPaletteOpen: false,
      selectedBlocks: [],
      
      setTheme: (theme) => set({ theme }),
      toggleSearch: () => set((state) => ({ searchOpen: !state.searchOpen })),
      setSearchQuery: (query) => set({ searchQuery: query }),
      toggleCommandPalette: () =>
        set((state) => ({ commandPaletteOpen: !state.commandPaletteOpen })),
      setSelectedBlocks: (blocks) => set({ selectedBlocks: blocks }),
      clearSelection: () => set({ selectedBlocks: [] }),
    }),
    {
      name: 'ui-store',
    }
  )
);
