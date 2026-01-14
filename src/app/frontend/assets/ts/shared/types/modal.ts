export interface ModalState {
  title: string | null;
  buttonText: string | null;
  isOpen: boolean;
}

export function createModalState(): ModalState {
  return {
    title: null,
    buttonText: null,
    isOpen: false,
  };
}

export function resetModal(modal: ModalState) {
  modal.title = null;
  modal.buttonText = null;
  modal.isOpen = false;
}
