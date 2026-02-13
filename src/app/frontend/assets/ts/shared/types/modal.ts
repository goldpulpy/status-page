export interface ModalState {
  title: string | null;
  buttonText: string | null;
  isOpen: boolean;
  isLoading: boolean;
}

export function createModalState(): ModalState {
  return {
    title: null,
    buttonText: null,
    isOpen: false,
    isLoading: false,
  };
}

export function resetModal(modal: ModalState) {
  modal.title = null;
  modal.buttonText = null;
  modal.isOpen = false;
  modal.isLoading = false;
}
