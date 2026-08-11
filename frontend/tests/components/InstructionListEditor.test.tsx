import React from 'react';
import { render, screen, fireEvent, act } from '../setup/test-utils';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import '@testing-library/jest-dom';
import InstructionListEditor from '../../src/components/InstructionListEditor';

// A real drag needs pointer and layout measurements jsdom does not provide, so
// the drag is driven through the onDragEnd handler dnd-kit would have called.
let dragEnd: ((event: any) => void) | undefined;

vi.mock('@dnd-kit/core', () => ({
  DndContext: ({ children, onDragEnd }: any) => {
    dragEnd = onDragEnd;
    return <>{children}</>;
  },
  closestCenter: vi.fn(),
  KeyboardSensor: vi.fn(),
  PointerSensor: vi.fn(),
  useSensor: vi.fn(),
  useSensors: vi.fn(() => []),
}));

vi.mock('@dnd-kit/sortable', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@dnd-kit/sortable')>();
  return {
    arrayMove: actual.arrayMove,
    SortableContext: ({ children }: any) => <>{children}</>,
    sortableKeyboardCoordinates: vi.fn(),
    verticalListSortingStrategy: vi.fn(),
    useSortable: () => ({
      attributes: {},
      listeners: {},
      setNodeRef: vi.fn(),
      transform: null,
      transition: undefined,
      isDragging: false,
    }),
  };
});

/** The sortable id of each rendered step, in display order. */
const stepIds = () =>
  screen.getAllByRole('textbox').map((element) => element.id.replace('instruction-', ''));

const stepValues = () =>
  screen.getAllByRole('textbox').map((element) => (element as HTMLTextAreaElement).value);

function ControlledEditor({ initial }: { initial: string[] }) {
  const [instructions, setInstructions] = React.useState(initial);
  return <InstructionListEditor instructions={instructions} onChange={setInstructions} />;
}

describe('InstructionListEditor', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    dragEnd = undefined;
  });

  describe('Rendering', () => {
    it('should render one step field per instruction', () => {
      render(<InstructionListEditor instructions={['Mix', 'Bake']} onChange={vi.fn()} />);

      expect(screen.getByPlaceholderText('Step 1...')).toHaveValue('Mix');
      expect(screen.getByPlaceholderText('Step 2...')).toHaveValue('Bake');
    });

    it('should render a drag handle for every step', () => {
      render(<InstructionListEditor instructions={['Mix', 'Bake', 'Serve']} onChange={vi.fn()} />);

      expect(screen.getAllByLabelText('Drag to reorder')).toHaveLength(3);
    });

    it('should not offer to remove the only step', () => {
      render(<InstructionListEditor instructions={['Mix']} onChange={vi.fn()} />);

      expect(screen.queryByTitle('Remove')).not.toBeInTheDocument();
    });

    it('should disable the fields and controls when disabled', () => {
      render(<InstructionListEditor instructions={['Mix', 'Bake']} onChange={vi.fn()} disabled />);

      expect(screen.getByPlaceholderText('Step 1...')).toBeDisabled();
      expect(screen.getByRole('button', { name: 'Add Step' })).toBeDisabled();
    });
  });

  describe('Editing', () => {
    it('should report an edited step', () => {
      const onChange = vi.fn();
      render(<InstructionListEditor instructions={['Mix', 'Bake']} onChange={onChange} />);

      fireEvent.change(screen.getByPlaceholderText('Step 2...'), { target: { value: 'Bake well' } });

      expect(onChange).toHaveBeenCalledWith(['Mix', 'Bake well']);
    });

    it('should append an empty step', () => {
      const onChange = vi.fn();
      render(<InstructionListEditor instructions={['Mix']} onChange={onChange} />);

      fireEvent.click(screen.getByRole('button', { name: 'Add Step' }));

      expect(onChange).toHaveBeenCalledWith(['Mix', '']);
    });

    it('should remove the selected step', () => {
      const onChange = vi.fn();
      render(<InstructionListEditor instructions={['Mix', 'Bake', 'Serve']} onChange={onChange} />);

      fireEvent.click(screen.getAllByTitle('Remove')[1]);

      expect(onChange).toHaveBeenCalledWith(['Mix', 'Serve']);
    });
  });

  describe('Reordering', () => {
    it('should move a dragged step to the drop position', () => {
      const onChange = vi.fn();
      render(<InstructionListEditor instructions={['Mix', 'Bake', 'Serve']} onChange={onChange} />);
      const [first, , third] = stepIds();

      dragEnd!({ active: { id: first }, over: { id: third } });

      expect(onChange).toHaveBeenCalledWith(['Bake', 'Serve', 'Mix']);
    });

    it('should move a step dragged upwards', () => {
      const onChange = vi.fn();
      render(<InstructionListEditor instructions={['Mix', 'Bake', 'Serve']} onChange={onChange} />);
      const [first, , third] = stepIds();

      dragEnd!({ active: { id: third }, over: { id: first } });

      expect(onChange).toHaveBeenCalledWith(['Serve', 'Mix', 'Bake']);
    });

    it('should ignore a step dropped onto itself', () => {
      const onChange = vi.fn();
      render(<InstructionListEditor instructions={['Mix', 'Bake']} onChange={onChange} />);
      const [first] = stepIds();

      dragEnd!({ active: { id: first }, over: { id: first } });

      expect(onChange).not.toHaveBeenCalled();
    });

    it('should ignore a step dropped outside the list', () => {
      const onChange = vi.fn();
      render(<InstructionListEditor instructions={['Mix', 'Bake']} onChange={onChange} />);
      const [first] = stepIds();

      dragEnd!({ active: { id: first }, over: null });

      expect(onChange).not.toHaveBeenCalled();
    });

    it('should keep each step id with its own text across a reorder', () => {
      render(<ControlledEditor initial={['Mix', 'Bake', 'Serve']} />);
      const idsBefore = stepIds();
      const mixId = idsBefore[0];

      act(() => dragEnd!({ active: { id: mixId }, over: { id: idsBefore[2] } }));

      expect(stepValues()).toEqual(['Bake', 'Serve', 'Mix']);
      expect(stepIds()).toEqual([idsBefore[1], idsBefore[2], mixId]);
    });

    it('should renumber the visible step labels after a reorder', () => {
      render(<ControlledEditor initial={['Mix', 'Bake', 'Serve']} />);
      const ids = stepIds();

      act(() => dragEnd!({ active: { id: ids[0] }, over: { id: ids[1] } }));

      expect(screen.getByPlaceholderText('Step 1...')).toHaveValue('Bake');
      expect(screen.getByPlaceholderText('Step 2...')).toHaveValue('Mix');
      expect(screen.getByPlaceholderText('Step 3...')).toHaveValue('Serve');
    });

    it('should give a step added from outside its own id', () => {
      const { rerender } = render(
        <InstructionListEditor instructions={['Mix']} onChange={vi.fn()} />
      );
      const [mixId] = stepIds();

      rerender(<InstructionListEditor instructions={['Mix', 'Bake']} onChange={vi.fn()} />);

      const ids = stepIds();
      expect(ids[0]).toBe(mixId);
      expect(ids[1]).not.toBe(mixId);
    });
  });
});
