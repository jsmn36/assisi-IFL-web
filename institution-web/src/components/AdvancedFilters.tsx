import { useState } from 'react';
import { Card, CardContent } from '@/components/Card';
import { Button } from '@/components/Button';
import { Input } from '@/components/Input';
import { Label } from '@/components/Label';
import { Select } from '@/components/Select';
import { Filter, X } from 'lucide-react';

interface FilterConfig {
  id: string;
  label: string;
  type: 'text' | 'select' | 'date' | 'dateRange';
  options?: Array<{ value: string; label: string }>;
}

interface AdvancedFiltersProps {
  filters: FilterConfig[];
  onFilterChange: (filters: Record<string, any>) => void;
  onReset: () => void;
}

export function AdvancedFilters({ filters, onFilterChange, onReset }: AdvancedFiltersProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [filterValues, setFilterValues] = useState<Record<string, any>>({});

  const handleFilterChange = (id: string, value: any) => {
    const newFilters = { ...filterValues, [id]: value };
    setFilterValues(newFilters);
    onFilterChange(newFilters);
  };

  const handleReset = () => {
    setFilterValues({});
    onReset();
  };

  const activeFilterCount = Object.values(filterValues).filter(v => v).length;

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => setIsExpanded(!isExpanded)}>
              <Filter className="h-4 w-4 mr-2" />
              Advanced Filters
              {activeFilterCount > 0 && (
                <span className="ml-2 bg-blue-100 text-blue-700 rounded-full px-2 py-0.5 text-xs">
                  {activeFilterCount}
                </span>
              )}
            </Button>
            {activeFilterCount > 0 && (
              <Button variant="ghost" size="sm" onClick={handleReset}>
                <X className="h-4 w-4 mr-1" />
                Clear All
              </Button>
            )}
          </div>

          {isExpanded && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t">
              {filters.map((filter) => (
                <div key={filter.id} className="space-y-2">
                  <Label htmlFor={filter.id}>{filter.label}</Label>
                  {filter.type === 'text' && (
                    <Input
                      id={filter.id}
                      value={filterValues[filter.id] || ''}
                      onChange={(e) => handleFilterChange(filter.id, e.target.value)}
                      placeholder={`Filter by ${filter.label.toLowerCase()}...`}
                    />
                  )}
                  {filter.type === 'select' && filter.options && (
                    <Select
                      id={filter.id}
                      value={filterValues[filter.id] || ''}
                      onChange={(e) => handleFilterChange(filter.id, e.target.value)}
                      options={[{ value: '', label: `All ${filter.label}` }, ...filter.options]}
                    />
                  )}
                  {filter.type === 'date' && (
                    <Input
                      id={filter.id}
                      type="date"
                      value={filterValues[filter.id] || ''}
                      onChange={(e) => handleFilterChange(filter.id, e.target.value)}
                    />
                  )}
                  {filter.type === 'dateRange' && (
                    <div className="flex gap-2">
                      <Input
                        type="date"
                        value={filterValues[`${filter.id}_start`] || ''}
                        onChange={(e) => handleFilterChange(`${filter.id}_start`, e.target.value)}
                        placeholder="Start"
                      />
                      <Input
                        type="date"
                        value={filterValues[`${filter.id}_end`] || ''}
                        onChange={(e) => handleFilterChange(`${filter.id}_end`, e.target.value)}
                        placeholder="End"
                      />
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}