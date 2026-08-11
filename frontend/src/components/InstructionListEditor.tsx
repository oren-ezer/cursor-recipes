import { useRef } from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import type { DragEndEvent } from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { GripVertical, X } from 'lucide-react';
import { Button } from './ui/button';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { useLanguage } from '../contexts/LanguageContext';

interface SortableInstructionProps {
  id: string;
  index: number;
  instruction: string;
  onChange: (index: number, value: string) => void;
  onRemove: (index: number) => void;
  disabled: boolean;
  canRemove: boolean;
}

function SortableInstruction({
  id,
  index,
  instruction,
  onChange,
  onRemove,
  disabled,
  canRemove,
}: SortableInstructionProps) {
  const { t } = useLanguage();
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id, disabled });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    zIndex: isDragging ? 1 : 0,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div ref={setNodeRef} style={style} className={`flex gap-4 items-start ${isDragging ? 'relative' : ''}`}>
      <div
        {...attributes}
        {...listeners}
        aria-label={t('recipe.form.drag_to_reorder')}
        title={t('recipe.form.drag_to_reorder')}
        className={`mt-8 touch-none ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-grab hover:text-primary'}`}
      >
        <GripVertical className="h-5 w-5 text-gray-400" />
      </div>

      <div className="flex-1 space-y-2">
        <Label htmlFor={`instruction-${id}`}>{t('recipe.form.step')} {index + 1}</Label>
        <Textarea
          id={`instruction-${id}`}
          value={instruction}
          onChange={(e) => onChange(index, e.target.value)}
          placeholder={`${t('recipe.form.step')} ${index + 1}...`}
          rows={2}
          required
          maxLength={2000}
          disabled={disabled}
          className={isDragging ? 'ring-2 ring-primary ring-offset-2' : ''}
        />
      </div>

      {canRemove && (
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={() => onRemove(index)}
          disabled={disabled}
          className="mt-8 text-destructive hover:text-destructive hover:bg-destructive/10"
          title={t('recipe.form.remove')}
        >
          <X className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
}

interface InstructionListEditorProps {
  instructions: string[];
  onChange: (instructions: string[]) => void;
  disabled?: boolean;
}

export default function InstructionListEditor({
  instructions,
  onChange,
  disabled = false,
}: InstructionListEditorProps) {
  const { t } = useLanguage();

  // Steps are plain strings, so they need a stable identity of their own for
  // drag-and-drop: reusing the index would make dnd-kit follow positions rather
  // than steps, breaking its drop animation and mid-drag tracking on reorder.
  // The ids live in a ref and move with the steps they belong to; every id
  // change is paired with an onChange, so the parent's re-render shows both.
  const idsRef = useRef<string[]>([]);
  const nextId = useRef(0);

  const createId = () => {
    nextId.current += 1;
    return `step-${nextId.current}`;
  };

  // Reconciled during render (not in an effect) so a step added from outside —
  // a recipe loading in, or AI image parsing filling the form — never renders a
  // frame without an id.
  if (idsRef.current.length !== instructions.length) {
    const ids = idsRef.current.slice(0, instructions.length);
    while (ids.length < instructions.length) {
      ids.push(createId());
    }
    idsRef.current = ids;
  }
  const ids = idsRef.current;

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 5,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const oldIndex = ids.indexOf(String(active.id));
    const newIndex = ids.indexOf(String(over.id));
    if (oldIndex === -1 || newIndex === -1) return;

    idsRef.current = arrayMove(ids, oldIndex, newIndex);
    onChange(arrayMove(instructions, oldIndex, newIndex));
  };

  const handleInstructionChange = (index: number, value: string) => {
    const newInstructions = [...instructions];
    newInstructions[index] = value;
    onChange(newInstructions);
  };

  const removeInstruction = (index: number) => {
    if (instructions.length <= 1) return;

    idsRef.current = ids.filter((_, i) => i !== index);
    onChange(instructions.filter((_, i) => i !== index));
  };

  const addInstruction = () => {
    idsRef.current = [...ids, createId()];
    onChange([...instructions, '']);
  };

  return (
    <div className="space-y-4">
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext items={ids} strategy={verticalListSortingStrategy}>
          {instructions.map((instruction, index) => (
            <SortableInstruction
              key={ids[index]}
              id={ids[index]}
              index={index}
              instruction={instruction}
              onChange={handleInstructionChange}
              onRemove={removeInstruction}
              disabled={disabled}
              canRemove={instructions.length > 1}
            />
          ))}
        </SortableContext>
      </DndContext>

      <Button
        type="button"
        variant="outline"
        onClick={addInstruction}
        disabled={disabled}
      >
        {t('recipe.form.add_step')}
      </Button>
    </div>
  );
}
