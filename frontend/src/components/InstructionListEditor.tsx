import { useState, useEffect, useRef } from 'react';
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
  } = useSortable({ id });

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
        className={`mt-8 cursor-grab hover:text-primary ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        title={t('recipe.form.drag_to_reorder')}
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
  
  // Keep track of stable IDs for the items
  const [items, setItems] = useState<{ id: string; text: string }[]>([]);
  const nextId = useRef(0);

  // Sync external instructions with internal items state
  useEffect(() => {
    setItems((prevItems) => {
      // If the lengths are the same, just update the text to avoid re-rendering issues
      if (prevItems.length === instructions.length) {
        return prevItems.map((item, index) => ({
          ...item,
          text: instructions[index]
        }));
      }
      
      // If lengths differ, we need to add or remove items
      // This is a simple approach: if we have more instructions, add new IDs
      // If we have fewer, truncate the IDs
      const newItems = instructions.map((text, index) => {
        if (index < prevItems.length) {
          return { ...prevItems[index], text };
        }
        nextId.current += 1;
        return { id: `step-${nextId.current}`, text };
      });
      return newItems;
    });
  }, [instructions]);

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

    if (over && active.id !== over.id) {
      const oldIndex = items.findIndex((item) => item.id === active.id);
      const newIndex = items.findIndex((item) => item.id === over.id);
      
      onChange(arrayMove(instructions, oldIndex, newIndex));
    }
  };

  const handleInstructionChange = (index: number, value: string) => {
    const newInstructions = [...instructions];
    newInstructions[index] = value;
    onChange(newInstructions);
  };

  const removeInstruction = (index: number) => {
    if (instructions.length > 1) {
      const newInstructions = instructions.filter((_, i) => i !== index);
      onChange(newInstructions);
    }
  };

  const addInstruction = () => {
    onChange([...instructions, '']);
  };

  return (
    <div className="space-y-4">
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext
          items={items.map(i => i.id)}
          strategy={verticalListSortingStrategy}
        >
          {items.map((item, index) => (
            <SortableInstruction
              key={item.id}
              id={item.id}
              index={index}
              instruction={item.text}
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
