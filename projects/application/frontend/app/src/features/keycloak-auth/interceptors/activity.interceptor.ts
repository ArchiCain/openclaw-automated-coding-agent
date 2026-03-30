import { inject } from '@angular/core';
import { HttpInterceptorFn } from '@angular/common/http';
import { tap } from 'rxjs/operators';
import { AuthService } from '../auth.service';

export const activityInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  auth.recordActivity();
  return next(req).pipe(tap({ next: () => {}, error: () => {} }));
};
